#!/usr/bin/env python3
"""Check substantive Sila-native SIP-1 process without foreign operational references."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_SECTIONS = (
    "What is an SIP?", "SIP Rationale", "SIP Types", "SIP Work Flow",
    "What belongs in a successful SIP?", "SIP Formats and Templates",
    "SIP Header Preamble", "Linking to External Resources",
    "Linking to other SIPs", "Auxiliary Files", "SIP Stewardship",
    "SIP Governance", "SIP Editors", "SIP Editor Responsibilities",
    "Style Guide", "Copyright",
)
STATES = ("Idea", "Draft", "Review", "Last Call", "Final", "Stagnant", "Withdrawn", "Living")
FIELDS = ("sip", "title", "description", "author", "discussions-to", "status",
          "last-call-deadline", "type", "category", "created", "requires", "withdrawal-reason")
REQUIRED_IDENTITIES = (
    "Sila Improvement Proposal",
    "Sila Virtual Machine (SVM)",
    "Sila Network (@sila-network)",
    "https://github.com/sila-network/SIPs",
    "https://sila-magicians.discourse.group/",
)

def check(s: str) -> list[str]:
    errors: list[str] = []
    header = re.search(r"\A---\n(.*?)\n---\n", s, re.S)
    if not header:
        return ["Missing YAML front matter"]
    front = dict(re.findall(r"^([a-z-]+):\s*(.*?)$", header.group(1), re.M))
    for k, v in (("sip", "1"), ("status", "Living"), ("type", "Meta"),
                 ("author", "Sila Network (@sila-network)")):
        if front.get(k) != v:
            errors.append(f"Wrong {k}")
    for h in REQUIRED_SECTIONS:
        if not re.search(r"^## " + re.escape(h) + r"$", s, re.M):
            errors.append(f"Missing section {h}")
    for state in STATES:
        if not re.search(r"^\*\*" + re.escape(state) + r"\*\* -", s, re.M):
            errors.append(f"Missing state {state}")
    for field in FIELDS:
        if not re.search(r"^" + re.escape(chr(96)+field+chr(96)+":") , s, re.M):
            errors.append(f"Missing field {field}")
    for identity in REQUIRED_IDENTITIES:
        if identity not in s:
            errors.append(f"Missing native Sila identity {identity}")
    if re.search(r"(?im)^## (history|archived|legacy)", s):
        errors.append("Forbidden historical section")
    if "github.com/sila-chain/" in s or "SIVM" in s:
        errors.append("Legacy operational identity")
    return errors

if __name__ == "__main__":
    issues = check((ROOT / "SIPS/sip-1.md").read_text(encoding="utf-8"))
    for item in issues:
        print("FAIL:", item)
    print(f"Reviewed {len(REQUIRED_SECTIONS)} process sections, {len(STATES)} states, {len(FIELDS)} fields")
    raise SystemExit(bool(issues))
