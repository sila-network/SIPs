"""Sila final audit: branch-protection contracts and Pure Sila identity gates.

Tests use synthetic rulesets only; they never assert a real GitHub approval or
modify any branch, governance record, or published document.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.sila import ROOT, audit
from tools.sila_review import load_policy
from tools.sila_closure import (
    ClosureError, assess_reviewer_roster, assess_rulesets, covers_default_branch,
    live_rulesets,
)


def safe_ruleset() -> dict:
    return {
        "id": 15,
        "name": "Sila test fixture",
        "enforcement": "active",
        "target": "branch",
        "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}},
        "bypass_actors": [],
        "rules": [
            {"type": "pull_request", "parameters": {
                "required_approving_review_count": 1,
                "dismiss_stale_reviews_on_push": True,
                "required_review_thread_resolution": True,
            }},
            {"type": "required_status_checks", "parameters": {
                "strict_required_status_checks_policy": True,
                "required_status_checks": [{"context": "native-checks"}],
            }},
            {"type": "required_linear_history"},
        ],
    }


def denied_word(encoded: str) -> str:
    return bytes.fromhex(encoded).decode("ascii")


class ClosureGateTests(unittest.TestCase):
    def test_current_reviewer_policy_is_not_authorized(self):
        blocked = assess_reviewer_roster(load_policy())
        self.assertEqual(len(blocked), 2)
        self.assertIn("editor", blocked[0])

    def test_current_account_cannot_review_itself(self):
        policy = deepcopy(load_policy())
        policy["reviewers"]["editor"] = ["sila-chain"]
        policy["reviewers"]["technical"] = ["sila-chain"]
        self.assertEqual(len(assess_reviewer_roster(policy)), 2)

    def test_real_nonoperator_logins_may_be_appointed_later(self):
        policy = deepcopy(load_policy())
        policy["reviewers"]["editor"] = ["example-reviewer"]
        policy["reviewers"]["technical"] = ["example-reviewer"]
        self.assertEqual(assess_reviewer_roster(policy), [])

    def test_no_rulesets_blocks_closure(self):
        self.assertIn("no active", assess_rulesets([])[0])

    def test_default_branch_matching(self):
        self.assertTrue(covers_default_branch(safe_ruleset()))

    def test_disabled_ruleset_is_ignored(self):
        fixture = safe_ruleset()
        fixture["enforcement"] = "disabled"
        self.assertIn("no active", assess_rulesets([fixture])[0])

    def test_nondefault_branch_rule_is_ignored(self):
        fixture = safe_ruleset()
        fixture["conditions"]["ref_name"]["include"] = ["refs/heads/temporary"]
        self.assertIn("no active", assess_rulesets([fixture])[0])

    def test_no_required_ci_check_is_a_blocker(self):
        fixture = safe_ruleset()
        fixture["rules"] = [r for r in fixture["rules"] if r["type"] != "required_status_checks"]
        self.assertTrue(any("native-checks" in x for x in assess_rulesets([fixture])))

    def test_wrong_ci_context_is_a_blocker(self):
        fixture = safe_ruleset()
        fixture["rules"][1]["parameters"]["required_status_checks"] = [{"context": "unknown-check"}]
        self.assertTrue(any("native-checks" in x for x in assess_rulesets([fixture])))

    def test_zero_approvals_is_a_blocker(self):
        fixture = safe_ruleset()
        fixture["rules"][0]["parameters"]["required_approving_review_count"] = 0
        self.assertTrue(any("zero" in x for x in assess_rulesets([fixture])))

    def test_no_stale_review_dismissal_is_a_blocker(self):
        fixture = safe_ruleset()
        fixture["rules"][0]["parameters"]["dismiss_stale_reviews_on_push"] = False
        self.assertTrue(any("stale reviews" in x for x in assess_rulesets([fixture])))

    def test_open_review_threads_block_release(self):
        fixture = safe_ruleset()
        fixture["rules"][0]["parameters"]["required_review_thread_resolution"] = False
        self.assertTrue(any("review threads" in x for x in assess_rulesets([fixture])))

    def test_non_linear_history_blocks_release(self):
        fixture = safe_ruleset()
        fixture["rules"] = [r for r in fixture["rules"] if r["type"] != "required_linear_history"]
        self.assertTrue(any("linear" in x for x in assess_rulesets([fixture])))

    def test_unverified_bypass_actors_block_release(self):
        fixture = safe_ruleset()
        fixture["bypass_actors"] = [{"actor_id": 1, "actor_type": "User", "bypass_mode": "always"}]
        self.assertTrue(any("bypass" in x for x in assess_rulesets([fixture])))

    def test_valid_simulated_ruleset_passes_preconditions_only(self):
        self.assertEqual(assess_rulesets([safe_ruleset()]), [])

    def test_invalid_git_approval_count_blocks(self):
        fixture = safe_ruleset()
        fixture["rules"][0]["parameters"]["required_approving_review_count"] = -1
        with self.assertRaises(ClosureError):
            assess_rulesets([fixture])

    def test_missing_github_ruleset_detail_is_not_silently_accepted(self):
        with patch("tools.sila_closure.github_get", side_effect=[
            [{"id": 6}], None,
        ]):
            with self.assertRaises(ClosureError):
                live_rulesets()

    def test_github_readonly_contract_uses_only_safe_read(self):
        from tools.sila_closure import github_get
        with self.assertRaises(ClosureError):
            github_get("/../danger")

    def test_project_sila_author_authority_is_unchanged(self):
        import tomllib
        config = tomllib.loads((ROOT / "config/sila.toml").read_text(encoding="utf-8"))
        self.assertEqual(config["governance"]["authorized_authors"],
                         ["Ahmed Ibrahim", "Jihad Mustafa"])

    def test_project_real_sip_one_remains_unapproved(self):
        from tools.sila_specs import validate_repository
        document = validate_repository(ROOT)
        self.assertEqual([metadata["sip"] for _, metadata, _ in document], ["1"])
        self.assertEqual(document[0][1]["status"], "Draft")
        self.assertNotIn("approval-ref", document[0][1])

    def test_pure_sila_audit_still_passes_real_source(self):
        self.assertEqual(audit(ROOT), 0)

    def test_standalone_foreign_protocol_words_are_detected(self):
        # Encoded negative fixtures avoid introducing an operational
        # foreign identity anywhere in the actual Sila-owned source text.
        samples = (
            "657468", "6574686572", "656970", "657263",
            "65766d", "77657468", "67657468", "736f6c6964697479",
        )
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "candidate.md"
            for encoded in samples:
                with self.subTest(encoded=encoded):
                    p.write_text("foreign protocol identifier: " + denied_word(encoded),
                                 encoding="utf-8")
                    self.assertGreater(audit(Path(directory)), 0)

    def test_identity_present_in_path_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            filename = denied_word("657468657265756d") + "-source.md"
            (Path(directory) / filename).write_text("Sila content", encoding="utf-8")
            self.assertGreater(audit(Path(directory)), 0)

    def test_independent_public_standards_are_not_false_positives(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "standards.md").write_text(
                "Independent public standards: https://www.w3.org and https://www.rfc-editor.org",
                encoding="utf-8",
            )
            self.assertEqual(audit(Path(directory)), 0)

    def test_disallowed_symlink_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            actual = root / "document.md"
            actual.write_text("Sila content", encoding="utf-8")
            (root / "linked.md").symlink_to(actual)
            self.assertGreater(audit(root), 0)


if __name__ == "__main__":
    unittest.main()
