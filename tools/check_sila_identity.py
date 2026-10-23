#!/usr/bin/env python3
"""Fail-closed audit for Sila names, source assets and unreviewed visuals.

An exact match is a review finding, not proof that a particular work is
infringing or that a technical replacement may safely be made.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

# Negative audit vocabulary is explicit fixture data, not a supported API,
# operational namespace, or compatibility shim. The exact fixture is exempt
# from scanning itself; all other source files remain subject to the audit.
_DENYLIST_RELATIVE_PATH = "tests/fixtures/sila-denied-identities.json"


def _load_denied_identities() -> dict[str, tuple[str, ...]]:
    fixture = Path(__file__).resolve().parent.parent / _DENYLIST_RELATIVE_PATH
    data = json.loads(fixture.read_text(encoding="utf-8"))
    expected = {
        "DISALLOWED_WORDS", "DISALLOWED_PREFIXES",
        "DISALLOWED_RPC_PREFIX", "DISALLOWED_TICKERS",
    }
    if not isinstance(data, dict) or set(data) != expected:
        raise ValueError("The Sila identity fixture has invalid keys")
    for name in expected:
        values = data[name]
        if (not isinstance(values, list) or not values
                or any(not isinstance(v, str) or not v for v in values)
                or len(set(values)) != len(values)):
            raise ValueError("The Sila identity fixture is missing valid terms: " + name)
    return {key: tuple(data[key]) for key in expected}


_DENIED = _load_denied_identities()
DISALLOWED_WORDS = _DENIED["DISALLOWED_WORDS"]
DISALLOWED_PREFIXES = _DENIED["DISALLOWED_PREFIXES"]
DISALLOWED_RPC_PREFIX = _DENIED["DISALLOWED_RPC_PREFIX"]
DISALLOWED_TICKERS = _DENIED["DISALLOWED_TICKERS"]
TEXT_SUFFIXES = {
    ".md", ".markdown", ".html", ".xml", ".csv", ".txt",
    ".py", ".go", ".sol", ".rs", ".js", ".json", ".jsonl",
    ".toml", ".yaml", ".yml", ".css", ".scss", ".svg",
    ".c", ".h", ".cpp", ".sh", ".patch", ".lock",
    ".rsp", ".yul", ".excalidraw", ".ld",
}
VISUAL_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".pdf"}
# A manual identity and copyright clearance must name the exact file bytes.
CLEARANCE_DOCUMENT = "VISUAL_CLEARANCES.json"
# Known non-Sila visual contents are blocked by byte fingerprint even when renamed.
KNOWN_FOREIGN_VISUAL_SHA256 = frozenset({
    "0dd6dce79ff18c5439d5ab6da086b7ac25f6442ee69facdae02ba83c3680e32a",
    "18a454c510efb078b619bf1af4a471cf072b568ef7518c9a70d434fc35680f06",
    "1a86a3309b2851aaa641daa50624d258a696f54d23f510833d781a54d229d364",
    "546d23b73f535788171b0cefa32620eb0e658e37c22b53edb213301925a25437",
    "5988c8da88c04c12e2b092c202b5d86ad5f2ee63c8ac02d2292a3c92809bed1c",
    "5e079ed5ee1c0152ddbbddb0cffad986d4de3f8005a5fa55e816b38f96a4bd86",
    "674d579fa176150657ee1de015f06ababf2e7cb3ced2881ed42ba318b65764cb",
    "6cb49e696e38353ac02fa03869d935bdb573c1b7eeb1d0aebfc5f0a6ef5e5ffd",
    "7ff96c1a734352a228adb641e4632ebc9d5ee2e44df04931d93f2fb95fbf9044",
    "aea28eb2d4bba97f61f6970d1fae0db88b4a0988f97e768417598c1f3a8e8603",
    "b2e35db24079f59daaa95dca3846032bb34297ef4e1aaaee6a01d83e333dc88e",
    "cacab9288d95f9addc53e9a391c7c57aa035399eae84e22a64d34b955de72a22",
    "cb5b9040160ff96aab4030d8e22c645f70243a21b1c66c6440632dd132811106",
    "e4e111fb608e380f7bb1ac4852298b929b6227a80ae52da19d6ba887a33d0a5f",
    "f6898d74e2fa56fd040d157baa92bb48731e2250b425148e952b0657f4cdf059",
})
BLOCK_PATTERN = re.compile(
    r"(?i:\b(?:" + "|".join(re.escape(word) for word in DISALLOWED_WORDS) + r")\b)"
    + r"|(?i:\b(?:" + "|".join(DISALLOWED_PREFIXES) + r")[-_\s#/0-9])"
    + r"|(?i:\b(?:" + "|".join(DISALLOWED_RPC_PREFIX) + r")_[a-z0-9_]+)"
    + r"|(?i:\b(?:" + "|".join(DISALLOWED_TICKERS) + r")\b)"
    + r"|(?:" + "|".join(part.upper() for part in DISALLOWED_PREFIXES) + r")(?=[A-Z0-9_])"
)


def audit(root: Path) -> dict:
    root = Path(root)
    term_hits: list[dict] = []
    visuals_unapproved: list[str] = []
    forbidden_visuals: list[str] = []
    counted: Counter[str] = Counter()
    raw_clearances = root / CLEARANCE_DOCUMENT
    clearances = {}
    if raw_clearances.exists():
        try:
            value = json.loads(raw_clearances.read_text(encoding="utf-8"))
            if not isinstance(value, dict):
                raise ValueError("Expected a mapping by asset path")
            clearances = value
        except (UnicodeError, json.JSONDecodeError, ValueError) as exc:
            term_hits.append({"file": CLEARANCE_DOCUMENT, "line": 0, "kind": "invalid-clearance", "match": str(exc)})
    for path in sorted(root.rglob("*")):
        if not path.is_file() or ".git" in path.parts:
            continue
        relative = path.relative_to(root).as_posix()
        # This one exact negative fixture contains the vocabulary to reject.
        # It is not a protocol identity, and no other fixture is exempted.
        if relative == _DENYLIST_RELATIVE_PATH:
            continue
        for matched in BLOCK_PATTERN.finditer(relative):
            term_hits.append({"file": relative, "line": 0, "kind": "path", "match": matched.group(0)})
        suffix = path.suffix.lower()
        if suffix in TEXT_SUFFIXES or path.name in {"Gemfile", "LICENSE", "Rakefile"}:
            counted["text_files"] += 1
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeError:
                term_hits.append({"file": relative, "line": 0, "kind": "encoding", "match": "invalid UTF-8"})
                continue
            for line_number, line in enumerate(text.splitlines(), 1):
                for matched in BLOCK_PATTERN.finditer(line):
                    term_hits.append({"file": relative, "line": line_number, "kind": "content", "match": matched.group(0)})
        if suffix in VISUAL_SUFFIXES:
            counted["visual_files"] += 1
            evidence = clearances.get(relative)
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest in KNOWN_FOREIGN_VISUAL_SHA256:
                forbidden_visuals.append(relative)
            if not (
                isinstance(evidence, dict)
                and evidence.get("sha256") == digest
                and evidence.get("identity_review") == "cleared"
                and isinstance(evidence.get("license_basis"), str)
                and evidence["license_basis"].strip()
                and isinstance(evidence.get("reviewed_by"), str)
                and evidence["reviewed_by"].strip()
                and isinstance(evidence.get("evidence_reference"), str)
                and evidence["evidence_reference"].strip()
            ):
                visuals_unapproved.append(relative)
    counted["path_or_text_findings"] = len(term_hits)
    counted["visuals_missing_clearance"] = len(visuals_unapproved)
    counted["forbidden_visuals"] = len(forbidden_visuals)
    return {
        "status": "BLOCKED" if term_hits or visuals_unapproved or forbidden_visuals else "TEXT_AND_VISUAL_AUDIT_PASS_ONLY",
        "counts": dict(counted),
        "term_hits": term_hits,
        "visuals_missing_clearance": visuals_unapproved,
        "forbidden_visuals": forbidden_visuals,
        "limitations": "Automated text checks and manual visual attestations do not establish protocol parity or legal ownership. PDFs may contain embedded text/graphics requiring independent examination.",
    }


def main() -> int:
    result = audit(Path(__file__).resolve().parent.parent)
    print("Sila identity review:", result["status"], result["counts"])
    for item in result["term_hits"][:15]:
        print("IDENTITY HOLD:", item["file"], item["line"], item["kind"], file=sys.stderr)
    for relative in result["forbidden_visuals"][:10]:
        print("FOREIGN GRAPHIC:", relative, file=sys.stderr)
    for relative in result["visuals_missing_clearance"][:10]:
        print("VISUAL HOLD:", relative, file=sys.stderr)
    return 1 if result["status"] == "BLOCKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())