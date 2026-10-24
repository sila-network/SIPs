#!/usr/bin/env python3
"""Enforce Sila adaptation bylines and the owner-authorized brand asset.

An issuer byline is not a claim of original authorship of upstream CC0 text.
The recorded adaptation provenance remains separate from these bylines.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

SILA_ISSUER = "Sila Network (@sila-network)"
LOGO_PATH = "assets/sila-logo.png"
LOGO_SHA256 = "26bf32c6fb7f76a8e6143dc1cd07c3839a6a7ff930d28498af7f5e5fd4e866da"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def check(root: Path) -> list[str]:
    """Return every owner-identity violation, without masking missing data."""
    root = Path(root)
    violations: list[str] = []
    proposals = sorted((root / "SIPS").glob("sip-*.md"))
    if not proposals:
        violations.append("No SIP documents found")
    for path in proposals:
        text = path.read_text(encoding="utf-8")
        front = re.match(r"\A---\r?\n(.*?)\r?\n---\r?\n", text, re.S)
        if not front:
            violations.append(f"{path.name}: malformed preamble")
            continue
        issuers = re.findall(r"^author:\s*(.*?)\s*$", front.group(1), re.M)
        if issuers != [SILA_ISSUER]:
            violations.append(f"{path.name}: expected one Sila Network adaptation issuer")

    logo = root / LOGO_PATH
    if not logo.is_file():
        violations.append("Official Sila logo missing")
        return violations
    content = logo.read_bytes()
    if not content.startswith(PNG_SIGNATURE):
        violations.append("Official Sila logo is not a PNG")
    digest = hashlib.sha256(content).hexdigest()
    if digest != LOGO_SHA256:
        violations.append("Official Sila logo bytes differ from owner-approved source")
    evidence = root / "VISUAL_CLEARANCES.json"
    if not evidence.is_file():
        violations.append("Brand rights/identity record missing")
        return violations
    try:
        register = json.loads(evidence.read_text(encoding="utf-8"))
        record = register.get(LOGO_PATH, {})
        if (not isinstance(record, dict) or record.get("sha256") != digest
                or record.get("identity_review") != "cleared"
                or not record.get("evidence_reference")):
            violations.append("Brand rights/identity record is absent or inconsistent")
    except (ValueError, UnicodeError, AttributeError):
        violations.append("Brand rights/identity register invalid")
    return violations


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    violations = check(root)
    for issue in violations:
        print("SILA ISSUER / BRAND FAIL:", issue, file=sys.stderr)
    print("Sila adaptation issuer and brand:", "PASS" if not violations else "FAIL")
    return int(bool(violations))


if __name__ == "__main__":
    raise SystemExit(main())