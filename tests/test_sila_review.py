"""Original review-system tests: no fabricated reviewers or automatic approvals."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import unittest
from unittest.mock import patch

from tools.sila_review import (
    ReviewError,
    approved_reviewers,
    canonical_path,
    classify_changes,
    evaluate_pr,
    final_owner_decision,
    load_final_owner,
    github_time,
    load_policy,
    require_reviews,
    urlopen,
)


HEAD = "f" * 40
OLD = "a" * 40


def review(login="verified-reviewer", state="APPROVED", sha=HEAD, ident=1):
    return {
        "id": ident,
        "user": {"login": login},
        "state": state,
        "commit_id": sha,
        "submitted_at": f"2026-11-05T12:00:{ident % 60:02d}Z",
    }


def owner_comment(decision="APPROVE", sha=HEAD, login="sila-chain", ident=200,
                  created="2026-11-05T12:01:00Z", updated=None):
    return {"id": ident, "user": {"login": login}, 
            "body": f"SILA FINAL {decision} {sha}",
            "created_at": created, "updated_at": updated or created}


def changed(path, status="modified", previous=None):
    result = {"filename": path, "status": status}
    if previous is not None:
        result["previous_filename"] = previous
    return result


def event(author="contributor", sha=HEAD, draft=False):
    return {
        "repository": {"full_name": "sila-network/SIPs"},
        "pull_request": {
            "number": 12,
            "draft": draft,
            "user": {"login": author},
            "base": {"repo": {"full_name": "sila-network/SIPs"}},
            "head": {"sha": sha},
        },
    }


def with_reviewers():
    p = deepcopy(load_policy())
    p["reviewers"]["editor"] = ["Sila-editor"]
    p["reviewers"]["technical"] = ["Sila-reviewer"]
    return p


class PolicyTests(unittest.TestCase):
    def test_real_sila_review_appointment_is_explicit_and_not_a_decision(self):
        roster = load_policy()["reviewers"]
        self.assertEqual(roster, {
            "editor": ["ahmed202225"],
            "technical": ["ahmed202225"],
        })
        self.assertNotIn("sila-chain", roster["editor"])
        self.assertNotIn("sila-chain", roster["technical"])

    def test_existing_policy_never_assumes_governance_role(self):
        p = load_policy()
        self.assertEqual(p["review"]["repository"], "sila-network/SIPs")
        self.assertEqual(p["review"]["spec_roles"], ["editor", "technical"])

    def test_invalid_repository_policy_is_rejected(self):
        p = deepcopy(load_policy())
        p["review"]["repository"] = "outside/other"
        self.assertRaises(ReviewError, self._validate_written, p)

    def test_duplicate_reviewer_is_rejected(self):
        p = deepcopy(load_policy())
        p["reviewers"]["editor"] = ["Sila-editor", "sila-editor"]
        self.assertRaises(ReviewError, self._validate_written, p)

    def test_missing_policy_role_is_rejected(self):
        p = deepcopy(load_policy())
        del p["reviewers"]["technical"]
        self.assertRaises(ReviewError, self._validate_written, p)

    def _validate_written(self, p):
        import tempfile
        from tools.sila_review import load_policy as load
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.toml"
            r = p["review"]
            a = p["reviewers"]
            def arr(seq):
                return "[" + ", ".join('"' + value + '"' for value in seq) + "]"
            path.write_text(
                "[review]\n"
                + f'repository = "{r["repository"]}"\n'
                + "".join(f"{key} = {arr(r[key])}\n" for key in ("spec_roles", "code_roles", "content_roles"))
                + "[reviewers]\n"
                + "".join(f"{key} = {arr(value)}\n" for key, value in a.items()),
                encoding="utf-8",
            )
            load(path)


class ChangeClassificationTests(unittest.TestCase):
    def setUp(self):
        self.p = load_policy()

    def test_spec_needs_editor_and_technical(self):
        roles, changed_policy, paths = classify_changes([changed("SIPS/sip-1.md")], self.p)
        self.assertEqual(roles, {"editor", "technical"})
        self.assertFalse(changed_policy)
        self.assertEqual(paths, ["SIPS/sip-1.md"])

    def test_tool_requires_technical(self):
        roles, blocked, _ = classify_changes([changed("tools/sila_review.py")], self.p)
        self.assertEqual(roles, {"technical"})
        self.assertFalse(blocked)

    def test_workflow_requires_technical(self):
        roles, _, _ = classify_changes([changed(".github/workflows/verify.yml")], self.p)
        self.assertEqual(roles, {"technical"})

    def test_readme_requires_editor(self):
        roles, _, _ = classify_changes([changed("README.md")], self.p)
        self.assertEqual(roles, {"editor", "technical"})

    def test_rename_covers_earlier_path(self):
        roles, _, paths = classify_changes([
            changed("misc/renamed.md", "renamed", "SIPS/sip-1.md"),
        ], self.p)
        self.assertEqual(roles, {"editor", "technical"})
        self.assertEqual(len(paths), 2)

    def test_review_policy_is_never_self_approving(self):
        roles, policy_changed, _ = classify_changes([
            changed("config/sila-review.toml"),
        ], self.p)
        self.assertTrue(policy_changed)
        self.assertIn("technical", roles)

    def test_initial_policy_creation_does_not_bypass_independent_review(self):
        roles, blocked, _ = classify_changes([
            changed("config/sila-review.toml", "added")
        ], self.p)
        self.assertFalse(blocked)
        self.assertEqual(roles, {"technical"})

    def test_existing_policy_update_still_blocked(self):
        _, blocked, _ = classify_changes([
            changed("config/sila-review.toml", "modified")
        ], self.p)
        self.assertTrue(blocked)

    def test_existing_policy_deletion_still_blocked(self):
        _, blocked, _ = classify_changes([
            changed("config/sila-review.toml", "removed")
        ], self.p)
        self.assertTrue(blocked)

    def test_new_policy_roster_without_authorized_reviewers_remains_blocked(self):
        with patch("tools.sila_review.github_pages", side_effect=[
            [changed("config/sila-review.toml", "added")],
            [],
        ]):
            empty = deepcopy(load_policy())
            empty["reviewers"] = {"editor": [], "technical": []}
            passed, messages = evaluate_pr(event(), empty, "token")
        self.assertFalse(passed)
        self.assertIn("technical", messages[0])

    def test_unsafe_traversal_path_rejected(self):
        for name in ("/etc/secrets", "../outside", "a/../c", "a\\b", ""):
            with self.subTest(name=name), self.assertRaises(ReviewError):
                canonical_path(name)

    def test_empty_changes_are_not_approved(self):
        with self.assertRaises(ReviewError):
            classify_changes([], self.p)

    def test_untrusted_changed_record_is_rejected(self):
        with self.assertRaises(ReviewError):
            classify_changes([{"status": "modified"}], self.p)


class ReviewDecisionTests(unittest.TestCase):
    def test_correct_commit_approved(self):
        self.assertEqual(approved_reviewers([review()], HEAD, "contributor"), {"verified-reviewer"})

    def test_old_commit_is_not_approved(self):
        self.assertEqual(approved_reviewers([review(sha=OLD)], HEAD, "contributor"), set())

    def test_author_cannot_approve_self(self):
        self.assertEqual(approved_reviewers([review(login="contributor")], HEAD, "contributor"), set())

    def test_changes_requested_cancels_approval(self):
        decisions = [review(ident=1), review(state="CHANGES_REQUESTED", ident=2)]
        self.assertEqual(approved_reviewers(decisions, HEAD, "contributor"), set())

    def test_review_dismissal_cancels_approval(self):
        decisions = [review(ident=1), review(state="DISMISSED", ident=2)]
        self.assertEqual(approved_reviewers(decisions, HEAD, "contributor"), set())

    def test_comment_does_not_reset_formal_approval(self):
        decisions = [review(ident=1), review(state="COMMENTED", ident=2)]
        self.assertEqual(approved_reviewers(decisions, HEAD, "contributor"), {"verified-reviewer"})

    def test_new_correct_head_approval_replaces_stale_one(self):
        decisions = [review(sha=OLD, ident=1), review(sha=HEAD, ident=2)]
        self.assertEqual(approved_reviewers(decisions, HEAD, "contributor"), {"verified-reviewer"})

    def test_invalid_commit_identifier_is_rejected(self):
        with self.assertRaises(ReviewError):
            approved_reviewers([review()], "not-a-commit", "contributor")

    def test_roster_without_appointments_blocks_all_roles(self):
        empty = deepcopy(load_policy())
        empty["reviewers"] = {"editor": [], "technical": []}
        passed, reasons = require_reviews(empty, {"editor", "technical"}, {"someone"})
        self.assertFalse(passed)
        self.assertEqual(len(reasons), 2)

    def test_one_reviewer_role_does_not_satisfy_two(self):
        p = with_reviewers()
        passed, reasons = require_reviews(p, {"editor", "technical"}, {"sila-editor"})
        self.assertFalse(passed)
        self.assertEqual(len(reasons), 1)
        self.assertIn("technical", reasons[0])

    def test_both_roles_pass_with_approved_reviewers(self):
        p = with_reviewers()
        passed, reasons = require_reviews(p, {"editor", "technical"}, {"sila-editor", "sila-reviewer"})
        self.assertTrue(passed)
        self.assertEqual(reasons, [])

    def test_one_authorized_person_can_cover_both_review_roles(self):
        p = with_reviewers()
        p["reviewers"]["technical"] = ["Sila-editor"]
        passed, reasons = require_reviews(p, {"editor", "technical"}, {"sila-editor"})
        self.assertTrue(passed)
        self.assertEqual(reasons, [])

    def test_both_roles_must_still_be_explicitly_authorized(self):
        p = with_reviewers()
        passed, reasons = require_reviews(p, {"editor", "technical"}, {"sila-editor"})
        self.assertFalse(passed)
        self.assertEqual(len(reasons), 1)

    def test_a_pr_author_cannot_approve_their_own_dual_role(self):
        p = with_reviewers()
        p["reviewers"]["technical"] = ["Sila-editor"]
        actual = approved_reviewers([review("Sila-editor")], HEAD, "Sila-editor")
        passed, reasons = require_reviews(p, {"editor", "technical"}, actual)
        self.assertFalse(passed)
        self.assertEqual(len(reasons), 2)

    def test_invalid_review_record_does_not_bypass_gate(self):
        with self.assertRaises(ReviewError):
            approved_reviewers([None], HEAD, "contributor")

    def test_login_matching_is_case_insensitive(self):
        p = with_reviewers()
        passed, _ = require_reviews(p, {"technical"}, {"SILA-REVIEWER".casefold()})
        self.assertTrue(passed)


class GithubEventTests(unittest.TestCase):
    def test_draft_pr_is_not_ready(self):
        with self.assertRaisesRegex(ReviewError, "draft pull request"):
            evaluate_pr(event(draft=True), load_policy(), "token")

    def test_other_repository_is_rejected(self):
        e = event()
        e["repository"]["full_name"] = "outside/network"
        with self.assertRaisesRegex(ReviewError, "unexpected repository"):
            evaluate_pr(e, load_policy(), "token")

    def test_missing_real_git_token_blocks(self):
        with self.assertRaises(ReviewError):
            evaluate_pr(event(), load_policy(), "")

    def test_missing_roster_causes_blocked_pr(self):
        with patch("tools.sila_review.github_pages", side_effect=[[changed("SIPS/sip-1.md")], []]):
            empty = deepcopy(load_policy())
            empty["reviewers"] = {"editor": [], "technical": []}
            passed, messages = evaluate_pr(event(), empty, "token")
        self.assertFalse(passed)
        self.assertEqual(len(messages), 2)

    def test_self_modifying_roster_cannot_pass(self):
        with patch("tools.sila_review.github_pages", return_value=[
            changed("config/sila-review.toml"),
        ]) as api:
            passed, reasons = evaluate_pr(event(), with_reviewers(), "token")
        self.assertFalse(passed)
        self.assertIn("cannot authorize itself", reasons[0])
        self.assertEqual(api.call_count, 1)

    def test_author_and_editor_separate_checks(self):
        with patch("tools.sila_review.github_pages", side_effect=[
            [changed("SIPS/sip-1.md")],
            [review("Sila-editor", ident=1), review("Sila-reviewer", ident=2)],
            [owner_comment()],
        ]):
            passed, reasons = evaluate_pr(event(), with_reviewers(), "token")
        self.assertTrue(passed)
        self.assertEqual(reasons, [])

    def test_outdated_approval_blocks(self):
        with patch("tools.sila_review.github_pages", side_effect=[
            [changed("tools/sila.py")],
            [review("Sila-reviewer", sha=OLD)],
        ]):
            passed, reasons = evaluate_pr(event(), with_reviewers(), "token")
        self.assertFalse(passed)
        self.assertIn("technical", reasons[0])



class OwnerDecisionTests(unittest.TestCase):
    def test_founder_is_exactly_configured(self):
        self.assertEqual(load_final_owner(), "sila-chain")

    def test_timestamp_needs_explicit_timezone(self):
        with self.assertRaises(ReviewError):
            github_time("2026-11-05T12:00:00")

    def test_no_owner_approval_blocks(self):
        passed, reasons = final_owner_decision([], HEAD, github_time("2026-11-05T12:00:03Z"))
        self.assertFalse(passed)
        self.assertIn("Ahmed Ibrahim", reasons[0])

    def test_authenticated_final_owner_decision_passes_after_review(self):
        passed, reasons = final_owner_decision([owner_comment()], HEAD, github_time("2026-11-05T12:00:03Z"))
        self.assertTrue(passed)
        self.assertEqual(reasons, [])

    def test_pr_author_is_not_permitted_as_technical_reviewer(self):
        self.assertEqual(approved_reviewers([review(login="sila-chain")], HEAD, "sila-chain"), set())

    def test_other_account_cannot_decide_for_ahmed(self):
        passed, _ = final_owner_decision(
            [owner_comment(login="not-owner")], HEAD, github_time("2026-11-05T12:00:03Z"))
        self.assertFalse(passed)

    def test_old_owner_approval_does_not_apply_to_new_revision(self):
        passed, _ = final_owner_decision([owner_comment(sha=OLD)], HEAD,
                                         github_time("2026-11-05T12:00:03Z"))
        self.assertFalse(passed)

    def test_owner_approval_before_independent_review_does_not_count(self):
        passed, reasons = final_owner_decision(
            [owner_comment()], HEAD, github_time("2026-11-05T12:02:00Z"))
        self.assertFalse(passed)
        self.assertIn("after", reasons[0])

    def test_owner_rejection_overrides_old_approval(self):
        passed, reasons = final_owner_decision([
            owner_comment(), owner_comment(decision="REJECT", ident=201,
                created="2026-11-05T12:02:00Z")], HEAD,
            github_time("2026-11-05T12:00:03Z"))
        self.assertFalse(passed)
        self.assertIn("not an approval", reasons[0])

    def test_owner_revocation_overrides_old_approval(self):
        passed, reasons = final_owner_decision([
            owner_comment(), owner_comment(decision="REVOKE", ident=201,
                created="2026-11-05T12:02:00Z")], HEAD,
            github_time("2026-11-05T12:00:03Z"))
        self.assertFalse(passed)
        self.assertIn("not an approval", reasons[0])

    def test_edited_owner_comment_is_rejected(self):
        with self.assertRaisesRegex(ReviewError, "edited Sila final decision"):
            final_owner_decision([
                owner_comment(updated="2026-11-05T12:03:00Z")], HEAD,
                github_time("2026-11-05T12:00:03Z"))

    def test_stray_text_is_not_final_owner_approval(self):
        passed, _ = final_owner_decision([
            {**owner_comment(), "body": "Looks good to me"}], HEAD,
            github_time("2026-11-05T12:00:03Z"))
        self.assertFalse(passed)

    def test_wrong_owner_account_is_rejected(self):
        with self.assertRaises(ReviewError):
            final_owner_decision([owner_comment()], HEAD, github_time("2026-11-05T12:00:03Z"), "other")

    def test_no_independent_review_never_reaches_owner_step(self):
        with patch("tools.sila_review.github_pages", side_effect=[
            [changed("SIPS/sip-1.md")], []
        ]):
            passed, reasons = evaluate_pr(event(), with_reviewers(), "token")
        self.assertFalse(passed)
        self.assertEqual(len(reasons), 2)

    def test_independent_review_without_ahmed_signoff_blocks(self):
        with patch("tools.sila_review.github_pages", side_effect=[
            [changed("SIPS/sip-1.md")],
            [review("Sila-editor", ident=1), review("Sila-reviewer", ident=2)],
            [],
        ]):
            passed, reasons = evaluate_pr(event(), with_reviewers(), "token")
        self.assertFalse(passed)
        self.assertIn("Ahmed Ibrahim", reasons[0])

    def test_ahmed_signoff_with_independent_technical_review_passes(self):
        with patch("tools.sila_review.github_pages", side_effect=[
            [changed("SIPS/sip-1.md")],
            [review("Sila-editor", ident=1), review("Sila-reviewer", ident=2)],
            [owner_comment()],
        ]):
            passed, reasons = evaluate_pr(event(), with_reviewers(), "token")
        self.assertTrue(passed)
        self.assertEqual(reasons, [])

if __name__ == "__main__":
    unittest.main()
