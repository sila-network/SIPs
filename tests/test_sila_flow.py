"""End-to-end Sila candidate lifecycle.

Every SIP-2/SIP-3 document and every simulated review exists only inside
TemporaryDirectory fixtures. This suite never issues a real proposal number,
appoints a GitHub reviewer, creates an approval or publishes a page.
"""

from __future__ import annotations

from datetime import date
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from xml.etree import ElementTree as ET

from tools.sila_review import ReviewError, evaluate_pr, load_policy


SOURCE = Path(__file__).resolve().parents[1]
REVISION = "b" * 40
OTHER_REVISION = "c" * 40

CANDIDATE_TEXT = """## Abstract

A separately proposed Sila interface for test-only integration checking.

## Motivation

Sila needs documented native interfaces and independent conformance criteria.

## Specification

The proposed Sila interface defines a request, an allowed response and
a failure outcome. It requires the existing Sila process in [SIP-1](sip-1.md#rationale).

## Rationale

Clear interface boundaries help independent Sila implementations agree.

## Test Cases

A valid request succeeds, and a malformed request is rejected safely.

## Security Considerations

Malformed inputs cannot change Sila-owned state without authorization.

## Copyright

Copyright (c) 2026 Sila Network. All rights reserved.
"""


def mock_event(author: str = "sila-chain", revision: str = REVISION) -> dict:
    return {
        "repository": {"full_name": "sila-network/SIPs"},
        "pull_request": {
            "number": 84,
            "draft": False,
            "user": {"login": author},
            "base": {"repo": {"full_name": "sila-network/SIPs"}},
            "head": {"sha": revision},
        },
    }


def mock_approval(actor: str, revision: str = REVISION, *, state: str = "APPROVED") -> dict:
    return {
        "id": 130,
        "user": {"login": actor},
        "commit_id": revision,
        "state": state,
        "submitted_at": "2026-11-05T12:00:00Z",
    }


class SilaLifecycleIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        space = tempfile.TemporaryDirectory(prefix="sila-flow-")
        self.addCleanup(space.cleanup)
        self.root = Path(space.name)
        for folder in ("SIPS", "config", "assets", "tools"):
            (self.root / folder).mkdir()
        for name in (
            "SIPS/sip-1.md",
            "config/sila.toml",
            "config/sila-review.toml",
            "assets/site.css",
            "assets/site.js",
            "tools/sila.py",
            "tools/sila_specs.py",
            "tools/sila_site.py",
            "tools/sila_review.py",
            "tools/__init__.py",
            "LICENSE.md",
        ):
            shutil.copy2(SOURCE / name, self.root / name)
        (self.root / "assets/sip-1").mkdir()
        shutil.copy2(SOURCE / "assets/sip-1/process.svg", self.root / "assets/sip-1/process.svg")
        self.candidate = self.root / "SIPS/sip-2.md"

    def propose(self, *, status: str = "Draft", category: str = "Interface",
                requires: str = "1", body: str = CANDIDATE_TEXT,
                extra_fields: dict[str, str] | None = None) -> None:
        meta = {
            "sip": "2",
            "title": "Sila Native Interface Test Candidate",
            "description": "Defines a test-only Sila interface for lifecycle verification.",
            "author": "Ahmed Ibrahim",
            "status": status,
            "type": "Standards Track",
            "category": category,
            "created": date.today().isoformat(),
            "requires": requires,
        }
        if extra_fields:
            meta.update(extra_fields)
        text = "---\n"
        text += "".join(f"{key}: {value}\n" for key, value in meta.items() if value is not None)
        text += "---\n\n" + body
        self.candidate.write_text(text, encoding="utf-8")

    def cmd(self, command: str, *, should_pass: bool = True) -> subprocess.CompletedProcess:
        child_env = dict(os.environ)
        child_env["PYTHONDONTWRITEBYTECODE"] = "1"
        result = subprocess.run(
            [sys.executable, str(self.root / "tools/sila.py"), command],
            cwd=self.root,
            env=child_env,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        if should_pass:
            self.assertEqual(result.returncode, 0, f"{command} failed: {result.stderr}\n{result.stdout}")
        else:
            self.assertNotEqual(result.returncode, 0, f"{command} unexpectedly passed")
            self.assertIn("BLOCKED:", result.stderr)
        return result

    def build(self) -> None:
        self.cmd("check")
        self.cmd("audit")
        self.cmd("build")
        self.cmd("verify-site")

    def policy(self, *, authorized: bool = False, dual_role: bool = False) -> dict:
        policy = load_policy(self.root / "config/sila-review.toml")
        if authorized:
            policy["reviewers"]["editor"] = ["sila-reviewer"]
            policy["reviewers"]["technical"] = ["sila-reviewer" if dual_role else "sila-technical"]
        return policy

    def review(self, *, authorized: bool = False, reviewer: str = "sila-reviewer",
               sha: str = REVISION, status: str = "APPROVED", author: str = "sila-chain",
               changed_path: str = "SIPS/sip-2.md",
               changed_status: str = "added") -> tuple[bool, list[str]]:
        files = [{"filename": changed_path, "status": changed_status}]
        responses = [files, [mock_approval(reviewer, sha, state=status)], [
            {"id": 901, "user": {"login": "sila-chain"},
             "body": f"SILA FINAL APPROVE {REVISION}",
             "created_at": "2026-11-05T12:02:00Z",
             "updated_at": "2026-11-05T12:02:00Z"}
        ]]
        with patch("tools.sila_review.github_pages", side_effect=responses):
            return evaluate_pr(mock_event(author), self.policy(authorized=authorized, dual_role=True), "fixture-only")

    def test_full_new_draft_creation_appears_everywhere(self) -> None:
        self.propose()
        self.build()
        home = (self.root / "_site/index.html").read_text()
        detail = (self.root / "_site/SIPS/sip-2.html").read_text()
        category = (self.root / "_site/categories/interface.html").read_text()
        status = (self.root / "_site/statuses/draft.html").read_text()
        search = json.loads((self.root / "_site/search.json").read_text())
        feed = ET.parse(self.root / "_site/feed.xml").getroot()
        self.assertIn("SIP-2", home)
        self.assertIn("Sila Native Interface Test Candidate", detail)
        self.assertIn("SIP-2", category)
        self.assertIn("SIP-2", status)
        self.assertEqual({item["number"] for item in search}, {1, 2})
        self.assertEqual(len(feed.findall("./channel/item")), 2)
        self.assertIn('href="sip-1.html#rationale"', detail)
        self.assertIn("Draft", detail)
        self.assertNotIn("Approved by", detail)

    def test_full_new_review_candidate_stays_unapproved(self) -> None:
        # A Review cannot depend normatively on SIP-1 while it is Draft.
        # This fixture covers an independent Sila proposal instead.
        self.propose(status="Review", requires=None,
                     body=CANDIDATE_TEXT.replace(
                         "It requires the existing Sila process in [SIP-1](sip-1.md#rationale).",
                         "It is an independent Sila proposal without normative dependencies."))
        self.build()
        self.assertIn("SIP-2", (self.root / "_site/statuses/review.html").read_text())
        self.assertNotIn("SIP-2", (self.root / "_site/statuses/final.html").read_text())
        self.assertIn("Review", (self.root / "_site/SIPS/sip-2.html").read_text())

    def test_separately_issued_conformance_candidate_has_correct_metadata(self) -> None:
        self.propose()
        self.build()
        data = json.loads((self.root / "_site/search.json").read_text())
        record = next(item for item in data if item["number"] == 2)
        self.assertEqual(record["category"], "Interface")
        self.assertEqual(record["author"], "Ahmed Ibrahim")
        self.assertEqual(record["status"], "Draft")
        self.assertEqual(record["path"], "SIPS/sip-2.html")

    def test_duplicate_number_and_filename_disagreement_blocks_pipeline(self) -> None:
        self.propose()
        self.candidate.write_text(self.candidate.read_text().replace("sip: 2", "sip: 1", 1))
        result = self.cmd("check", should_pass=False)
        self.assertIn("number differs", result.stderr)

    def test_unissued_dependency_blocks_pipeline(self) -> None:
        self.propose(requires="99119")
        self.cmd("check", should_pass=False)

    def test_unissued_inline_reference_blocks_pipeline(self) -> None:
        self.propose(body=CANDIDATE_TEXT.replace("SIP-1", "SIP-3333"))
        self.cmd("check", should_pass=False)

    def test_invalid_relative_document_link_blocks_pipeline(self) -> None:
        self.propose(body=CANDIDATE_TEXT.replace("sip-1.md#rationale", "missing.md"))
        self.cmd("check", should_pass=False)

    def test_circular_sila_dependency_blocks_pipeline(self) -> None:
        self.propose(requires="3")
        other = self.root / "SIPS/sip-3.md"
        other.write_text(self.candidate.read_text().replace("sip: 2", "sip: 3", 1)
                         .replace("requires: 3", "requires: 2", 1))
        self.cmd("check", should_pass=False)

    def test_apparently_final_status_is_not_approvable(self) -> None:
        self.propose(status="Final", extra_fields={"approval-ref": "https://github.com/sila-network/SIPs"})
        result = self.cmd("check", should_pass=False)
        self.assertIn("not yet independently verifiable", result.stderr)

    def test_incorrect_author_blocks_pipeline(self) -> None:
        self.propose(extra_fields={"author": "Unapproved Name"})
        self.cmd("check", should_pass=False)

    def test_unapproved_changed_sip_has_no_review_pass(self) -> None:
        self.propose()
        self.build()
        allowed, blockers = self.review()
        self.assertFalse(allowed)
        self.assertEqual(len(blockers), 2)

    def test_synthetic_independent_review_covers_declared_roles(self) -> None:
        self.propose()
        self.build()
        allowed, blockers = self.review(authorized=True)
        self.assertTrue(allowed)
        self.assertEqual(blockers, [])
        self.assertEqual(load_policy(self.root / "config/sila-review.toml")["reviewers"]["editor"], ["ahmed202225"])

    def test_synthetic_review_does_not_authorize_self_approval(self) -> None:
        self.propose()
        self.build()
        allowed, blockers = self.review(authorized=True, author="sila-reviewer")
        self.assertFalse(allowed)
        self.assertTrue(blockers)

    def test_synthetic_stale_review_does_not_pass(self) -> None:
        self.propose()
        self.build()
        allowed, blockers = self.review(authorized=True, sha=OTHER_REVISION)
        self.assertFalse(allowed)
        self.assertTrue(blockers)

    def test_synthetic_requested_changes_does_not_pass(self) -> None:
        self.propose()
        self.build()
        allowed, blockers = self.review(authorized=True, status="CHANGES_REQUESTED")
        self.assertFalse(allowed)
        self.assertTrue(blockers)

    def test_editing_review_policy_cannot_auto_authorize_its_change(self) -> None:
        allowed, blockers = self.review(
            authorized=True, changed_path="config/sila-review.toml",
            changed_status="modified"
        )
        self.assertFalse(allowed)
        self.assertIn("cannot authorize itself", blockers[0])

    def test_sila_review_policy_has_appointment_not_automatic_approval(self) -> None:
        result = subprocess.run(
            [sys.executable, str(self.root / "tools/sila_review.py"), "policy"],
            cwd=self.root, capture_output=True, text=True, check=False, timeout=20
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("appointments are not approvals", result.stdout)

    def test_pr_without_event_is_blocked(self) -> None:
        result = subprocess.run(
            [sys.executable, str(self.root / "tools/sila_review.py"), "pull-request", "--event", str(self.root / "missing.json")],
            cwd=self.root, capture_output=True, text=True, check=False, timeout=20
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("REVIEW BLOCKED:", result.stderr)

    def test_remove_trial_candidate_restores_exact_offline_catalog(self) -> None:
        self.propose()
        self.build()
        self.candidate.unlink()
        self.build()
        data = json.loads((self.root / "_site/search.json").read_text())
        self.assertEqual([item["number"] for item in data], [1])
        self.assertFalse((self.root / "_site/SIPS/sip-2.html").exists())
        self.assertFalse((self.root / "_site/categories/interface.html").read_text().find("SIP-2") != -1)

    def test_real_repository_never_contains_test_only_proposals(self) -> None:
        self.assertFalse((SOURCE / "SIPS/sip-2.md").exists())
        self.assertFalse((SOURCE / "SIPS/sip-3.md").exists())


if __name__ == "__main__":
    unittest.main()
