"""Sila-native proposal syntax, semantics, references, and dependency validator.

Uses only the Python standard library. This verifier does not claim that a
governance vote, discussion, approval or activation really took place.
"""
from __future__ import annotations
from datetime import date
from pathlib import Path
import json
import math
import re
import tomllib
from urllib.parse import urlsplit, unquote


class ProposalError(ValueError):
    """A Sila proposal fails a mandatory rule."""


FIELDS = frozenset((
    "sip", "title", "description", "author", "status", "type", "category",
    "created", "requires", "discussions-to", "last-call-deadline",
    "withdrawal-reason", "approval-ref", "implementation-ref",
))
MANDATORY = ("sip", "title", "description", "author", "status", "type", "created")
HEADER_ORDER = (
    "sip", "title", "description", "author", "discussions-to", "status",
    "last-call-deadline", "type", "category", "created", "requires",
    "withdrawal-reason", "approval-ref", "implementation-ref",
)
MAX_TITLE = 44
MAX_DESCRIPTION = 140
# Section semantics and dependency maturity are Sila-native acceptance rules.
# The two optional migration sections express Sila-specific upgrade impact.
SECTION_ORDER = (
    "Abstract", "Motivation", "Specification", "Rationale",
    "Backwards Compatibility", "Migration", "Rollback Plan",
    "Test Cases", "Reference Implementation", "Security Considerations",
    "Copyright",
)
STATUS_MATURITY = {
    "Idea": 0, "Draft": 1, "Stagnant": 1,
    "Review": 2, "Last Call": 3, "Final": 4, "Living": 4,
    "Withdrawn": 0,
}
PINNED_SILA_REFERENCE = re.compile(
    r"/sila-network/[a-zA-Z0-9_.-]+/(?:blob|tree|commit)/[a-fA-F0-9]{40}(?:/[^?#]+)?\Z"
)
FILENAME = re.compile(r"sip-([1-9][0-9]*)\.md\Z")
PREAMBLE_LINE = re.compile(r"([a-z][a-z-]*):[ \t]+(.+)\Z")
LINK = re.compile(r"!?\[[^\]\n]*\]\(([^)\s]+)\)")
REFERENCE = re.compile(r"\bSIP-([0-9]+)\b")
LINKED_SILA_REFERENCE = re.compile(r"(?<!!)\[(SIP-[1-9][0-9]*)\]\(([^)\s]+)\)")
FENCE = re.compile(r"^[ \t]{0,3}(\x60{3,}|~{3,})")
HEADING = re.compile(r"^## ([^\n]+?)[ \t]*$")
ANCHOR_HEADING = re.compile(r"^#{1,4}[ \t]+(.+?)[ \t]*$")
BAD_SILA_NUMBER = re.compile(
    r"(?<![A-Za-z0-9])SIP(?:[ \t]+(?:-[ \t]*)?|[ \t]*-[ \t]+)(?:0|[1-9][0-9]*)\b"
    r"|(?<![A-Za-z0-9])SIP[0-9]+\b"
    r"|(?<![A-Za-z0-9])SIP-0[0-9]+\b",
    re.IGNORECASE,
)
MALFORMED_HEADING = re.compile(r"^[ \t]{0,3}#{1,6}(?![ \t#])")
# CSL is an independently governed bibliographic standard, not a Sila identity.
CSL_TYPES = frozenset((
    "article", "article-journal", "article-magazine", "article-newspaper",
    "bill", "book", "broadcast", "chapter", "classic", "collection",
    "dataset", "document", "entry", "entry-dictionary", "entry-encyclopedia",
    "event", "figure", "graphic", "hearing", "interview", "legal_case",
    "legislation", "manuscript", "map", "motion_picture", "musical_score",
    "pamphlet", "paper-conference", "patent", "performance", "periodical",
    "personal_communication", "post", "post-weblog", "regulation",
    "report", "review", "review-book", "software", "song", "speech",
    "standard", "thesis", "treaty", "webpage",
))


def reject(path: Path, reason: str) -> None:
    raise ProposalError(f"{path.name}: {reason}")


def read_document(path: Path) -> tuple[dict[str, str], str]:
    if path.stat().st_size > 1_000_000:
        reject(path, "document exceeds one megabyte")
    lines = path.read_text(encoding="utf-8").replace("\r\n", "\n").splitlines()
    if len(lines) < 4 or lines[0] != "---":
        reject(path, "missing opening metadata delimiter")
    try:
        end = lines.index("---", 1)
    except ValueError:
        reject(path, "missing closing metadata delimiter")
    meta: dict[str, str] = {}
    for row, line in enumerate(lines[1:end], start=2):
        found = PREAMBLE_LINE.fullmatch(line)
        if not found:
            reject(path, f"invalid flat metadata line {row}")
        key, value = found.groups()
        if key not in FIELDS or key in meta:
            reject(path, f"unknown or duplicate metadata key {key}")
        if value != value.strip() or value.startswith(("[", "{", "|", ">", "&", "*", "!", "'", '"')):
            reject(path, f"unsupported scalar value for {key}")
        if any(ord(char) < 32 for char in value):
            reject(path, f"control character in {key}")
        meta[key] = value
    if list(meta) != sorted(meta, key=HEADER_ORDER.index):
        reject(path, "Sila metadata fields are out of canonical order")
    return meta, "\n".join(lines[end + 1:]) + "\n"


def parse_date(path: Path, value: str, name: str) -> date:
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        reject(path, f"{name} is not an ISO date")
    try:
        return date.fromisoformat(value)
    except ValueError:
        reject(path, f"invalid {name} date")


def allowed_url(url: str, settings: dict, *, discussion: bool = False) -> bool:
    try:
        obj = urlsplit(url)
        port = obj.port
    except ValueError:
        return False
    if obj.scheme != "https" or not obj.hostname or obj.username or obj.password:
        return False
    if port not in (None, 443):
        return False
    if obj.hostname not in settings["references"]["allowed_web_hosts"]:
        return False
    # All URL authority checks are syntax checks, not proof of live sources.
    if obj.hostname == "github.com":
        # Encoded and relative path components can escape the apparent
        # organizational namespace in a browser or an HTTP client.
        if "%" in obj.path:
            return False
        parts = obj.path.split("/")
        if any(part in (".", "..") for part in parts) or len(parts) < 3:
            return False
        if parts[1] == "sila-network":
            if not parts[2] or parts[2] in (".", ".."):
                return False
        else:
            allowed_repos = settings["references"]["independent_standard_repositories"]
            project = "/".join(parts[1:3])
            if project not in allowed_repos:
                return False
            if not re.fullmatch(
                r"/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/blob/[a-fA-F0-9]{40}/[^?#]+",
                obj.path,
            ) or obj.query or obj.fragment:
                return False
    if obj.hostname == "www.rfc-editor.org":
        if not re.fullmatch(r"/rfc/rfc[1-9][0-9]*(?:\.html)?", obj.path):
            return False
    if obj.hostname == "www.w3.org":
        if not re.fullmatch(r"/TR/[0-9]{4}/[A-Za-z0-9._/-]+/?", obj.path):
            return False
    if obj.hostname == "html.spec.whatwg.org":
        if not re.fullmatch(r"/commit-snapshots/[a-fA-F0-9]{40}/", obj.path):
            return False
    if obj.hostname == "www.unicode.org":
        if not re.fullmatch(r"/reports/tr[0-9]+/tr[0-9]+-[0-9]+\.html", obj.path):
            return False
    if discussion:
        return (obj.hostname == "sila-magicians.discourse.group"
                and re.fullmatch(r"/t/[a-zA-Z0-9_-]+/[1-9][0-9]*/?", obj.path) is not None
                and not obj.fragment)
    return True


def strip_inline_code(line: str) -> str:
    """Ignore inline code examples when checking external links and references."""
    return re.sub(r"(?<!`)(`+)(?!`).*?\1(?!`)", "", line)


def visible_markdown(body: str) -> tuple[list[str], list[str], str]:
    """Remove fenced examples before inspecting headings and references."""
    headings: list[str] = []
    links: list[str] = []
    visible: list[str] = []
    opened = ""
    width = 0
    for line in body.splitlines():
        match = FENCE.match(line)
        if match:
            seq = match.group(1)
            if not opened:
                opened, width = seq[0], len(seq)
            elif seq[0] == opened and len(seq) >= width and not line[match.end():].strip():
                opened, width = "", 0
            continue
        if opened:
            continue
        visible.append(line)
        h = HEADING.fullmatch(line)
        if h:
            headings.append(h.group(1).strip())
        links.extend(LINK.findall(strip_inline_code(line)))
    if opened:
        raise ProposalError("unclosed Sila documentation code fence")
    return headings, links, "\n".join(visible)


# These field groups implement the independent CSL JSON item data model.
# Sila owns its validator, while CSL remains an external data standard.
CSL_STRING_FIELDS = frozenset((
    "type", "citation-key", "language", "journalAbbreviation",
    "shortTitle", "abstract", "annote", "archive", "archive_collection",
    "archive_location", "archive-place", "authority", "call-number",
    "citation-label", "collection-title", "container-title",
    "container-title-short", "dimensions", "division", "DOI", "event",
    "event-title", "event-place", "genre", "ISBN", "ISSN", "jurisdiction",
    "keyword", "medium", "note", "original-publisher",
    "original-publisher-place", "original-title", "part-title", "PMCID",
    "PMID", "publisher", "publisher-place", "references",
    "reviewed-genre", "reviewed-title", "scale", "section", "source",
    "status", "title", "title-short", "URL", "version",
    "volume-title", "volume-title-short", "year-suffix",
))
CSL_NAME_FIELDS = frozenset((
    "author", "chair", "collection-editor", "compiler", "composer",
    "container-author", "contributor", "curator", "director",
    "editor", "editorial-director", "executive-producer", "guest",
    "host", "interviewer", "illustrator", "narrator", "organizer",
    "original-author", "performer", "producer", "recipient",
    "reviewed-author", "script-writer", "series-creator", "translator",
))
CSL_DATE_FIELDS = frozenset((
    "accessed", "available-date", "event-date", "issued",
    "original-date", "submitted",
))
CSL_NUMBER_FIELDS = frozenset((
    "chapter-number", "citation-number", "collection-number",
    "edition", "first-reference-note-number", "issue", "locator",
    "number", "number-of-pages", "number-of-volumes", "page",
    "page-first", "part", "printing", "supplement", "volume",
))
CSL_NAME_STRING = frozenset((
    "family", "given", "dropping-particle", "non-dropping-particle",
    "suffix", "literal",
))
CSL_NAME_FLEX = frozenset(("comma-suffix", "static-ordering", "parse-names"))
CSL_DATE_STRING = frozenset(("literal", "raw"))
CSL_DATE_FLEX = frozenset(("season", "circa"))
CSL_FIELDS = (CSL_STRING_FIELDS | CSL_NAME_FIELDS | CSL_DATE_FIELDS
              | CSL_NUMBER_FIELDS | {"id", "categories", "custom"})


def csl_scalar(value: object) -> bool:
    """CSL mixed-value fields accept text or finite numbers, never booleans."""
    return (
        isinstance(value, str)
        or type(value) is int
        or type(value) is float and math.isfinite(value)
    )


def safe_citation_url(value: object) -> bool:
    """Accept only syntactically safe HTTPS addresses without credentials."""
    if (not isinstance(value, str) or not value.strip()
            or any(character.isspace() or character == "\\" for character in value)):
        return False
    try:
        parsed = urlsplit(value)
        return (
            parsed.scheme == "https" and bool(parsed.hostname)
            and not parsed.username and not parsed.password
            and parsed.port in (None, 443)
        )
    except ValueError:
        return False


def check_csl_names(path: Path, value: object) -> None:
    if not isinstance(value, list):
        reject(path, "invalid independent CSL citation name list")
    for person in value:
        if (not isinstance(person, dict)
                or any(
                    (key in CSL_NAME_STRING and not isinstance(item, str))
                    or (key in CSL_NAME_FLEX and not (
                        csl_scalar(item) or isinstance(item, bool)
                    ))
                    or (key not in CSL_NAME_STRING and key not in CSL_NAME_FLEX)
                    for key, item in person.items()
                )):
            reject(path, "invalid independent CSL citation name variable")


def check_csl_date(path: Path, value: object) -> None:
    if not isinstance(value, dict):
        reject(path, "invalid independent CSL citation date variable")
    for key, item in value.items():
        if key in CSL_DATE_STRING:
            valid = isinstance(item, str)
        elif key in CSL_DATE_FLEX:
            valid = csl_scalar(item) or isinstance(item, bool)
        elif key == "date-parts":
            valid = (
                isinstance(item, list) and 1 <= len(item) <= 2
                and all(isinstance(part, list) and 1 <= len(part) <= 3
                        and all(csl_scalar(number) for number in part)
                        for part in item)
            )
        else:
            valid = False
        if not valid:
            reject(path, "invalid independent CSL citation date variable")


def check_citation_json(path: Path, source: str) -> None:
    """Validate an independent CSL JSON array with Sila-native restrictions."""
    def unique_object(pairs: list[tuple[str, object]]) -> dict:
        value: dict = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("duplicate JSON field")
            value[key] = item
        return value

    def reject_non_json_number(value: str) -> None:
        raise ValueError("nonfinite JSON number")

    try:
        record = json.loads(
            source, object_pairs_hook=unique_object,
            parse_constant=reject_non_json_number,
        )
    except (ValueError, TypeError) as error:
        reject(path, f"invalid Sila citation JSON: {error}")
    if not isinstance(record, list):
        reject(path, "Sila citation JSON must contain a list of CSL records")
    for citation in record:
        if not isinstance(citation, dict):
            reject(path, "Sila citation list must contain CSL objects")
        check_citation_record(path, citation)


def check_citation_record(path: Path, record: dict) -> None:
    """Validate recognized CSL field groups, including nested name and date data."""
    if (not isinstance(record.get("type"), str)
            or record["type"] not in CSL_TYPES):
        reject(path, "Sila citation type is not a valid independent CSL type")
    identifier = record.get("id")
    if not csl_scalar(identifier) or (
        isinstance(identifier, str) and not identifier.strip()
    ):
        reject(path, "Sila citation needs a valid identifier")
    if not isinstance(record.get("DOI"), str) or not record["DOI"].strip():
        reject(path, "Sila citation must include a DOI")
    url = record.get("URL")
    if not isinstance(url, str) or not url.strip():
        reject(path, "Sila citation must include a URL")
    if not safe_citation_url(url):
        reject(path, "Sila citation URL must use safe HTTPS")

    for key, value in record.items():
        if key not in CSL_FIELDS:
            reject(path, f"unknown independent CSL citation field {key}")
        if key in CSL_STRING_FIELDS:
            if not isinstance(value, str):
                reject(path, f"invalid independent CSL string field {key}")
        elif key in CSL_NUMBER_FIELDS:
            if not csl_scalar(value):
                reject(path, f"invalid independent CSL number field {key}")
        elif key in CSL_NAME_FIELDS:
            check_csl_names(path, value)
        elif key in CSL_DATE_FIELDS:
            check_csl_date(path, value)
        elif key == "categories":
            if not isinstance(value, list) or not all(
                isinstance(item, str) for item in value
            ):
                reject(path, "invalid independent CSL categories")
        elif key == "custom":
            if not isinstance(value, dict):
                reject(path, "invalid Sila citation custom data")
            if "additional-urls" in value:
                links = value["additional-urls"]
                if not isinstance(links, list) or any(
                    not safe_citation_url(item) for item in links
                ):
                    reject(path, "invalid Sila citation additional URLs")


def check_citation_blocks(path: Path, body: str) -> None:
    """Read structured citation examples only from explicitly labeled fences."""
    opened = ""
    width = 0
    language = ""
    lines: list[str] = []
    for line in body.splitlines():
        marker = FENCE.match(line)
        if marker:
            sequence = marker.group(1)
            if not opened:
                opened, width = sequence[0], len(sequence)
                language = line[marker.end():].strip().lower()
                lines = []
            elif sequence[0] == opened and len(sequence) >= width and not line[marker.end():].strip():
                if language == "csl-json":
                    check_citation_json(path, "\n".join(lines))
                opened, width, language, lines = "", 0, "", []
            elif language == "csl-json":
                lines.append(line)
            continue
        if opened and language == "csl-json":
            lines.append(line)
    if opened:
        reject(path, "unclosed Sila citation or documentation code fence")


def check_markdown_conventions(path: Path, visible: str) -> None:
    """Check Sila prose without treating code examples as live references."""
    for line in visible.splitlines():
        prose = strip_inline_code(line)
        # Markdown may contain examples of other syntax inside code, but
        # hidden comments must never suppress real Sila review text.
        if "<!--" in prose or "-->" in prose:
            reject(path, "raw HTML comments are not valid Sila specification prose")
        if MALFORMED_HEADING.match(line):
            reject(path, "Sila Markdown headings require a space after the marker")
        if BAD_SILA_NUMBER.search(prose):
            reject(path, "Sila proposal references must use canonical SIP-N notation")
        if re.search(r"[\u2018\u2019\u201c\u201d]", prose):
            reject(path, "Sila normative Markdown must use straight quotation marks")
        if re.match(r"^[ \t]{0,3}#{5,6}[ \t]", line):
            reject(path, "Sila renderer supports headings up to four levels")


def slug(title: str) -> str:
    """Match the original Sila site renderer for Unicode and punctuation."""
    result = re.sub(r"[^\w -]", "", title.lower()).strip().replace(" ", "-")
    return result or "section"


def anchors_for_document(body: str) -> set[str]:
    """Reproduce the site's generated anchors, including repeated headings."""
    _, _, visible = visible_markdown(body)
    names: set[str] = set()
    counts: dict[str, int] = {}
    for line in visible.splitlines():
        header = ANCHOR_HEADING.fullmatch(line)
        if header:
            base = slug(header.group(1))
            counts[base] = counts.get(base, 0) + 1
            names.add(base if counts[base] == 1 else f"{base}-{counts[base]}")
    return names


def check_link(root: Path, document: Path, value: str, settings: dict) -> None:
    try:
        parsed = urlsplit(value)
    except ValueError:
        reject(document, f"malformed link {value}")
    if parsed.scheme or parsed.netloc:
        if not allowed_url(value, settings):
            reject(document, f"unsafe or unauthorized external link {value}")
        return
    if value.startswith(("/", "//")) or "\\" in value:
        reject(document, f"unsafe local link {value}")
    if re.search(r"%(?![0-9a-fA-F]{2})", value):
        reject(document, f"invalid encoded link {value}")
    raw_path = unquote(parsed.path)
    target = (document.parent / raw_path).resolve() if raw_path else document.resolve()
    if not target.is_relative_to(root.resolve()) or not target.is_file():
        reject(document, f"unresolved or escaping local link {value}")
    if parsed.fragment:
        if target.suffix.lower() != ".md":
            reject(document, f"unsupported anchor in {value}")
        content = read_document(target)[1] if target.parent == root / "SIPS" else target.read_text(encoding="utf-8")
        anchors = anchors_for_document(content)
        if unquote(parsed.fragment) not in anchors:
            reject(document, f"unresolved heading anchor {value}")


def check_first_sila_reference(path: Path, visible: str, current: int) -> None:
    """A first external SIP citation must identify its own verified local source.

    Only text outside fenced and inline examples counts. The ordinary link
    resolver performs the separate existence and anchor checks.
    """
    seen: set[int] = set()
    for line in visible.splitlines():
        content = strip_inline_code(line)
        citations = list(LINKED_SILA_REFERENCE.finditer(content))
        for reference in REFERENCE.finditer(content):
            number = int(reference.group(1))
            if number == current or number in seen:
                continue
            seen.add(number)
            expected = f"sip-{number}.md"
            for citation in citations:
                if citation.start(1) != reference.start():
                    continue
                href = citation.group(2)
                parsed = urlsplit(href)
                if (not parsed.scheme and not parsed.netloc
                        and not parsed.query
                        and parsed.path.rsplit("/", 1)[-1] == expected):
                    break
            else:
                reject(path, f"first Sila reference SIP-{number} must link to its own document")


def check_metadata(path: Path, meta: dict[str, str], settings: dict) -> int:
    match = FILENAME.fullmatch(path.name)
    if not match:
        reject(path, "noncanonical Sila proposal filename")
    number = int(match.group(1))
    for key in MANDATORY:
        if not meta.get(key):
            reject(path, f"missing required field {key}")
    if meta["sip"] != str(number):
        reject(path, "Sila proposal number differs from filename")
    if len(meta["title"]) > MAX_TITLE or len(meta["description"]) > MAX_DESCRIPTION:
        reject(path, "title or description too long")
    if len(meta["title"].strip()) < 2 or len(meta["description"].strip()) < 2:
        reject(path, "title or description is shorter than the required minimum")
    if BAD_SILA_NUMBER.search(meta["title"] + " " + meta["description"]):
        reject(path, "Sila metadata references must use canonical SIP-N notation")
    if re.search(r"\bSIP-[1-9][0-9]*\b", meta["title"], re.IGNORECASE):
        reject(path, "title must not repeat the Sila proposal number")
    if ":" in meta["title"] or ":" in meta["description"]:
        reject(path, "Sila title and description must not contain a colon")
    governance = settings["governance"]
    if meta["status"] not in governance["statuses"]:
        reject(path, "unrecognized Sila status")
    if meta["type"] not in governance["types"]:
        reject(path, "unrecognized Sila document type")
    authors = [item.strip() for item in meta["author"].split(",")]
    if len(authors) != len(set(authors)) or any(item not in governance["authorized_authors"] for item in authors):
        reject(path, "unapproved or duplicated Sila author")
    if number == 1 and authors != ["Ahmed Ibrahim", "Jihad Mustafa"]:
        reject(path, "SIP-1 author byline differs from the Sila foundation")
    if meta["type"] == "Standards Track":
        if meta.get("category") not in governance["categories"]:
            reject(path, "Standards Track requires a valid category")
    elif "category" in meta:
        reject(path, "category only applies to Standards Track")
    created = parse_date(path, meta["created"], "created")
    if created > date.today():
        reject(path, "proposal creation date is in the future")
    if meta["status"] == "Last Call":
        if not meta.get("last-call-deadline") or not meta.get("discussions-to"):
            reject(path, "Last Call needs deadline and real discussion topic")
        deadline = parse_date(path, meta["last-call-deadline"], "last-call-deadline")
        if deadline < created or deadline < date.today():
            reject(path, "Last Call deadline is past or before creation")
    elif "last-call-deadline" in meta:
        reject(path, "Last Call date must not appear in another status")
    if meta["status"] == "Withdrawn":
        if not meta.get("withdrawal-reason"):
            reject(path, "Withdrawn requires a withdrawal reason")
    elif "withdrawal-reason" in meta:
        reject(path, "withdrawal reason on a non-Withdrawn proposal")
    if meta["status"] == "Living" and meta["type"] != "Meta":
        reject(path, "Living only applies to approved Sila process proposals")
    if meta["status"] in {"Final", "Living"}:
        if not meta.get("approval-ref"):
            reject(path, "approved status requires a decision reference")
        reject(path, "Sila decision authority is not yet independently verifiable")
    if "approval-ref" in meta:
        reject(path, "unapproved proposal cannot claim an approval reference")
    if meta.get("discussions-to") and not allowed_url(meta["discussions-to"], settings, discussion=True):
        reject(path, "invalid Sila discussion topic URL")
    if meta.get("implementation-ref"):
        value = meta["implementation-ref"]
        if not allowed_url(value, settings):
            reject(path, "invalid Sila implementation reference")
        parsed = urlsplit(value)
        if (parsed.hostname != "github.com" or parsed.query or parsed.fragment
                or not PINNED_SILA_REFERENCE.fullmatch(parsed.path)):
            reject(path, "Sila implementation reference must use an immutable commit")
    return number


def check_sections(path: Path, headings: list[str], body: str, meta: dict, settings: dict) -> None:
    expected = settings["governance"]["required_sections"]
    if any(headings.count(name) != 1 for name in expected):
        reject(path, "missing or duplicate mandatory Sila sections")
    indexes = [headings.index(name) for name in expected]
    if indexes != sorted(indexes):
        reject(path, "mandatory Sila sections are out of order")
    for title in expected:
        section = re.search(r"^## " + re.escape(title) + r"[ \t]*\n(.*?)(?=^## |\Z)", body, re.M | re.S)
        if section is None:
            reject(path, f"missing section {title}")
        text = re.sub(r"[\s#*\x60-]+", "", section.group(1))
        if len(text) < 12 or text.upper() in {"TBD", "NA", "NEEDSDISCUSSION"}:
            reject(path, f"empty or placeholder section {title}")
    if meta["type"] == "Standards Track" and meta["status"] not in {"Idea", "Draft"}:
        if headings.count("Test Cases") != 1:
            reject(path, "reviewed Sila standard needs Test Cases")
    if len(headings) != len(set(headings)):
        reject(path, "duplicate Sila top-level section")
    if any(title not in SECTION_ORDER for title in headings):
        reject(path, "unrecognized Sila top-level section")
    sequence = [SECTION_ORDER.index(title) for title in headings]
    if sequence != sorted(sequence):
        reject(path, "Sila document sections are out of canonical order")
    # The preview renderer does not support loose introductory prose before
    # the first normative section. Reject rather than silently reordering it.
    first_content = next((line for line in body.splitlines() if line.strip()), "")
    if first_content.strip() != "## Abstract":
        reject(path, "Sila normative text must start with the Abstract heading")


def check_requires(path: Path, meta: dict) -> list[int]:
    if "requires" not in meta:
        return []
    values = [item.strip() for item in meta["requires"].split(",")]
    if any(re.fullmatch(r"[1-9][0-9]*", item) is None for item in values):
        reject(path, "invalid Sila requires list")
    ids = [int(x) for x in values]
    if len(ids) != len(set(ids)):
        reject(path, "duplicate normative dependency")
    if ids != sorted(ids):
        reject(path, "Sila normative dependencies must be in ascending order")
    if int(meta["sip"]) in ids:
        reject(path, "Sila proposal cannot require itself")
    return ids


def check_cycles(graph: dict[int, list[int]]) -> None:
    visiting: set[int] = set()
    visited: set[int] = set()
    def walk(number: int) -> None:
        if number in visiting:
            raise ProposalError(f"cyclic Sila proposal dependencies at SIP-{number}")
        if number in visited:
            return
        visiting.add(number)
        for child in graph[number]:
            walk(child)
        visiting.remove(number)
        visited.add(number)
    for number in sorted(graph):
        walk(number)


def validate_repository(root: Path) -> list[tuple[Path, dict[str, str], str]]:
    root = root.resolve()
    settings = tomllib.loads((root / "config" / "sila.toml").read_text(encoding="utf-8"))
    folder = root / "SIPS"
    if folder.is_symlink():
        raise ProposalError("Sila proposal directory cannot be a symbolic link")
    if not folder.is_dir():
        raise ProposalError("Sila proposal directory is missing")
    # Only actual, flat, canonical source documents may enter the validator.
    # Symlinks and alternate-cased extensions must never bypass verification.
    for entry in folder.iterdir():
        if entry.is_symlink():
            reject(entry, "symbolic link is not a Sila proposal source")
        if entry.is_dir():
            reject(entry, "nested Sila proposal directories are not supported")
        if entry.is_file() and entry.suffix.lower() == ".md" and entry.suffix != ".md":
            reject(entry, "noncanonical Sila proposal filename extension")
    paths = sorted(folder.glob("*.md"))
    if not paths:
        raise ProposalError("no Sila proposal documents")
    found: dict[int, tuple[Path, dict[str, str], str]] = {}
    dependencies: dict[int, list[int]] = {}
    for path in paths:
        meta, body = read_document(path)
        number = check_metadata(path, meta, settings)
        if number in found:
            reject(path, "duplicated proposal number")
        found[number] = path, meta, body
        dependencies[number] = check_requires(path, meta)
    if 1 not in found:
        raise ProposalError("Sila governance foundation SIP-1 is absent")
    for number, (path, meta, body) in found.items():
        headings, links, visible = visible_markdown(body)
        check_citation_blocks(path, body)
        check_markdown_conventions(path, visible)
        check_sections(path, headings, visible, meta, settings)
        for required in dependencies[number]:
            if required not in found:
                reject(path, f"missing Sila normative dependency {required}")
            dependency_status = found[required][1]["status"]
            if dependency_status == "Withdrawn":
                reject(path, f"withdrawn Sila normative dependency {required}")
            if STATUS_MATURITY[dependency_status] < STATUS_MATURITY[meta["status"]]:
                reject(path, f"Sila normative dependency SIP-{required} has insufficient status")
        reference_text = "\n".join(strip_inline_code(line) for line in visible.splitlines())
        for referenced in REFERENCE.findall(reference_text + "\n" + meta["description"]):
            target = int(referenced)
            if target not in found:
                reject(path, f"unknown Sila cross-reference SIP-{referenced}")
            if target == number:
                continue
            referenced_status = found[target][1]["status"]
            if referenced_status == "Withdrawn":
                reject(path, f"withdrawn Sila cross-reference SIP-{target}")
            if STATUS_MATURITY[referenced_status] < STATUS_MATURITY[meta["status"]]:
                reject(path, f"Sila cross-reference SIP-{target} has insufficient status")
        check_first_sila_reference(path, visible, number)
        if meta["type"] == "Standards Track":
            match = re.search(
                r"^## Specification[ \t]*\n(.*?)(?=^## |\Z)",
                reference_text, re.M | re.S,
            )
            specification = match.group(1) if match else ""
            for referenced in REFERENCE.findall(specification):
                target = int(referenced)
                if target != number and target not in dependencies[number]:
                    reject(path, f"Sila specification requires undeclared normative SIP-{target}")
        for value in links:
            check_link(root, path, value, settings)
    check_cycles(dependencies)
    return [found[num] for num in sorted(found)]
