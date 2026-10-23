#!/usr/bin/env python3
"""Conservative, fail-closed rights review for Sila standards staging.

A clean scan is not a legal opinion or permission from rightsholders.
Unverified third-party materials block the release rather than being silently
assumed to have the same license as the repository root.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


PDF_SUFFIX = ".pdf"
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".svg"}
# Explicitly known conditional licenses must remain disclosed. These checks are
# provenance safeguards, not confirmations that the underlying rights are owned
# by Sila or that any external publisher granted adaptation permissions.
REQUIRED_NOTICES: dict[str, tuple[str, ...]] = {
    "assets/sip-8222/poseidon/poseidon.pdf": ("Lorenzo Grassi", "CC BY 4.0"),
    "assets/sip-8222/customizable-constraint-systems/customizable-constraint-systems.pdf": ("Srinath Setty", "CC BY 4.0"),
    "assets/sip-8222/evolving-nullifiers/evolving-nullifiers.pdf": ("Sean Bowe", "CC BY-NC-ND 4.0"),
    "assets/sip-7577/semver.md": ("Tom Preston-Werner", "CC BY 3.0"),
    "SIPS/sip-1355.md": ("Paweł Bylica", "CC BY-NC-SA 4.0"),
    "SIPS/sip-1485.md": ("trustfarm", "CC BY-NC-SA 4.0"),
    "assets/sip-7885/solidity/src/ZKNOX_NTT.sol": ("Renaud Dubois", "MIT"),
    "SIPS/sip-6789.md": ("AGPL-3.0",),
}

RESTRICTED_LICENSE_TERMS = (
    "Attribution-NonCommercial-ShareAlike",
    "Attribution-NonCommercial-NoDerivatives",
)


def review(root: Path) -> list[str]:
    findings: list[str] = []
    license_path = root / "LICENSE.md"
    if not license_path.is_file() or "CC0 1.0 Universal" not in license_path.read_text(encoding="utf-8"):
        findings.append("Missing or unexpected general legal text in LICENSE.md")

    for path in sorted((root / "SIPS").glob("sip-*.md")):
        value = path.read_text(encoding="utf-8")
        for term in RESTRICTED_LICENSE_TERMS:
            if term in value:
                findings.append(f"{path.relative_to(root)}: restricted per-document terms {term}")
        if "SPDX-License-Identifier: AGPL-3.0" in value:
            findings.append(f"{path.relative_to(root)}: embedded code with separate AGPL-3.0 notice")
        if path.name != "sip-1.md" and not re.search(r"(?im)^#{1,4}\s*Copyright\b", value):
            if not re.search(r"(?m)^reference_kind:\s*src\s*$", value):
                findings.append(f"{path.relative_to(root)}: no explicit individual copyright or waiver section")

    assets = root / "assets"
    if assets.is_dir():
        for path in sorted(assets.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(root)
            if path.suffix.lower() == PDF_SUFFIX:
                findings.append(f"{relative}: PDF permission for Sila adaptation not verified")
            if path.name == "LICENSE":
                text = path.read_text(encoding="utf-8", errors="replace")
                for term in RESTRICTED_LICENSE_TERMS:
                    if term in text:
                        findings.append(f"{relative}: restricted third-party license {term}")
            if path.suffix.lower() == ".md":
                text = path.read_text(encoding="utf-8", errors="replace")
                if re.search(r"CC BY 3\.0|creativecommons\.org/licenses/by/3\.0", text, flags=re.I):
                    findings.append(f"{relative}: third-party CC BY 3.0 attribution not cleared")
            if path.name != "LICENSE" and path.suffix.lower() != PDF_SUFFIX:
                # Source-copied assets require positive, per-file evidence for
                # unrestricted Sila republication or modification. A generic
                # license at repository root does not prove their rights.
                if path.suffix.lower() not in {".sol"}:
                    asset_text = ""
                    if path.suffix.lower() not in IMAGE_SUFFIXES:
                        try:
                            asset_text = path.read_text(encoding="utf-8")
                        except (UnicodeError, OSError):
                            pass
                    if "SPDX-License-Identifier: CC0-1.0" not in asset_text and not re.search(r"Copyright and related rights waived via \[CC0\]", asset_text):
                        findings.append(f"{relative}: positive supporting-asset rights clearance missing")
                else:
                    code_text = path.read_text(encoding="utf-8", errors="replace")
                    if not re.search(r"SPDX-License-Identifier:\s*(?:MIT|CC0-1.0)\b", code_text):
                        findings.append(f"{relative}: positive code rights clearance missing")
            if path.suffix.lower() == ".sol":
                text = path.read_text(encoding="utf-8", errors="replace")
                if "SPDX-License-Identifier: MIT" in text:
                    ancestors = [path.parent, *path.parents]
                    in_assets = [p for p in ancestors if p == assets or assets in p.parents]
                    if not any((p / "LICENSE").is_file() and "MIT License" in (p / "LICENSE").read_text(encoding="utf-8", errors="replace") for p in in_assets):
                        findings.append(f"{relative}: MIT permission notice not found in its asset hierarchy")
    notices_path = root / "THIRD_PARTY_NOTICES.md"
    present = {path: expected for path, expected in REQUIRED_NOTICES.items() if (root / path).exists()}
    if present:
        if not notices_path.is_file():
            findings.append("Missing THIRD_PARTY_NOTICES.md for imported, differently licensed works")
        else:
            notices = notices_path.read_text(encoding="utf-8")
            for path, markers in present.items():
                if path not in notices:
                    # A group notice can cover source files collectively if their
                    # parent directory and the credited people/license are present.
                    if path.endswith("/ZKNOX_NTT.sol") and "assets/sip-7885/solidity/src/ZKNOX_NTT.sol" in notices:
                        pass
                    else:
                        findings.append(f"{path}: individual rights entry missing in THIRD_PARTY_NOTICES.md")
                for marker in markers:
                    if marker not in notices:
                        findings.append(f"{path}: missing required {marker} in rights register")

    for relative in (
        "assets/sip-7885/solidity/src/ZKNOX_NTT.sol",
        "assets/sip-7885/solidity/test/ZKNOX_NTT.t.sol",
        "assets/sip-7885/solidity/test/ZKNOX_NTT_DilithiumField.t.sol",
    ):
        source = root / relative
        if source.is_file():
            code = source.read_text(encoding="utf-8")
            for marker in ("Renaud Dubois", "Simon Masson", "SPDX-License-Identifier: MIT"):
                if marker not in code:
                    findings.append(f"{relative}: original MIT copyright or license marker missing: {marker}")

    return findings


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    findings = review(root)
    for finding in findings:
        print("LEGAL HOLD:", finding, file=sys.stderr)
    print(f"Sila rights clearance: {len(findings)} unresolved issues. Not a legal opinion.")
    return int(bool(findings))


if __name__ == "__main__":
    raise SystemExit(main())
