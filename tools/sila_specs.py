"""Sila-native proposal syntax, semantics, references, and dependency validator.

Uses only the Python standard library. This verifier does not claim that a
governance vote, discussion, approval or activation really took place.
"""
from __future__ import annotations
from datetime import date
from pathlib import Path
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
FENCE = re.compile(r"^[ \t]{0,3}(\x60{3,}|~{3,})")
HEADING = re.compile(r"^## ([^\n]+?)[ \t]*$")
ANCHOR_HEADING = re.compile(r"^#{1,4}[ \t]+(.+?)[ \t]*$")


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
    if not folder.is_dir():
        raise ProposalError("Sila proposal directory is missing")
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
        for referenced in REFERENCE.findall(reference_text):
            if int(referenced) not in found:
                reject(path, f"unknown Sila cross-reference SIP-{referenced}")
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
