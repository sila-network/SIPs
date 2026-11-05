#!/usr/bin/env python3
"""Read-only Sila readiness audit; prints blockers and never records an approval.

This gate is deliberately separate from normal code CI. A successful build is
not evidence of independent reviewers, a protected default branch, or an
approved Sila governance decision. No result is persisted in the repository.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

if __package__:
    from .sila_review import load_policy, ReviewError
else:
    from sila_review import load_policy, ReviewError

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "sila-network/SIPs"
DEFAULT_BRANCH = "main"
EXPECTED_CHECK = "native-checks"
CURRENT_OPERATOR = "sila-chain"
API_ROOT = f"https://api.github.com/repos/{REPOSITORY}"


class ClosureError(ValueError):
    """A release requirement could not be checked reliably."""


def assess_reviewer_roster(policy: dict) -> list[str]:
    """An account named on the roster is not by itself a human approval."""
    problems: list[str] = []
    required = policy["review"]["spec_roles"]
    for role in required:
        accounts = {login.casefold() for login in policy["reviewers"][role]}
        if not accounts:
            problems.append(f"Sila {role} reviewer has not been appointed")
        elif not (accounts - {CURRENT_OPERATOR}):
            problems.append(f"Sila {role} role has no reviewer independent of {CURRENT_OPERATOR}")
    return problems


def covers_default_branch(entry: dict) -> bool:
    if entry.get("enforcement") != "active" or entry.get("target") != "branch":
        return False
    included = entry.get("conditions", {}).get("ref_name", {}).get("include", [])
    excluded = entry.get("conditions", {}).get("ref_name", {}).get("exclude", [])
    candidates = {"~DEFAULT_BRANCH", f"refs/heads/{DEFAULT_BRANCH}"}
    return bool(candidates.intersection(included)) and not candidates.intersection(excluded)


def assess_rulesets(entries: list[dict]) -> list[str]:
    """Evaluate the effective documented controls in active main rulesets."""
    if not isinstance(entries, list) or any(not isinstance(item, dict) for item in entries):
        raise ClosureError("GitHub ruleset data is incomplete")
    matched = [item for item in entries if covers_default_branch(item)]
    if not matched:
        return ["no active GitHub ruleset covers Sila main"]
    contexts: set[str] = set()
    approval_numbers: list[int] = []
    stale_dismissal = False
    thread_resolution = False
    linear_history = False
    bypasses = False
    for entry in matched:
        if entry.get("bypass_actors"):
            bypasses = True
        for rule in entry.get("rules", []):
            kind = rule.get("type")
            params = rule.get("parameters") or {}
            if kind == "required_status_checks":
                for required in params.get("required_status_checks", []):
                    if isinstance(required, dict) and isinstance(required.get("context"), str):
                        contexts.add(required["context"])
            elif kind == "pull_request":
                count = params.get("required_approving_review_count", 0)
                if not isinstance(count, int) or isinstance(count, bool) or count < 0:
                    raise ClosureError("invalid GitHub approval count")
                approval_numbers.append(count)
                stale_dismissal = stale_dismissal or params.get("dismiss_stale_reviews_on_push") is True
                thread_resolution = thread_resolution or params.get("required_review_thread_resolution") is True
            elif kind == "required_linear_history":
                linear_history = True
    problems = []
    if EXPECTED_CHECK not in contexts:
        problems.append(f"GitHub main does not require the {EXPECTED_CHECK} check")
    if not approval_numbers or max(approval_numbers) < 1:
        problems.append("GitHub main requires zero verified human approvals")
    if not stale_dismissal:
        problems.append("GitHub main does not dismiss stale reviews on new commits")
    if not thread_resolution:
        problems.append("GitHub main does not require review threads to be resolved")
    if not linear_history:
        problems.append("GitHub main does not require linear commit history")
    if bypasses:
        problems.append("GitHub main has an unverified bypass actor")
    return problems


def github_get(path: str, token: str = "") -> object:
    if not path.startswith("/") or "?" in path or ".." in path:
        raise ClosureError("unsafe GitHub audit path")
    headers = {"Accept": "application/vnd.github+json",
               "X-GitHub-Api-Version": "2022-11-28",
               "User-Agent": "sila-closure-readonly"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(API_ROOT + path, headers=headers)
    try:
        with urlopen(request, timeout=20) as response:
            return json.load(response)
    except (HTTPError, URLError, TimeoutError, ValueError) as error:
        raise ClosureError("cannot read current Sila GitHub protection state") from error


def live_rulesets(token: str = "") -> list[dict]:
    listing = github_get("/rulesets", token)
    if not isinstance(listing, list):
        raise ClosureError("unexpected GitHub ruleset listing")
    entries: list[dict] = []
    for item in listing:
        if not isinstance(item, dict) or not isinstance(item.get("id"), int):
            raise ClosureError("invalid GitHub ruleset reference")
        detail = github_get(f'/rulesets/{item["id"]}', token)
        if not isinstance(detail, dict):
            raise ClosureError("invalid GitHub ruleset details")
        entries.append(detail)
    return entries


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Sila final-closure readiness")
    parser.add_argument("command", choices=("check",))
    args = parser.parse_args()
    try:
        policy = load_policy()
        problems = assess_reviewer_roster(policy)
        problems.extend(assess_rulesets(live_rulesets(os.getenv("GITHUB_TOKEN", ""))))
        if problems:
            for problem in problems:
                print("SILA CLOSURE BLOCKED:", problem)
            print(f"BLOCKED: {len(problems)} unfulfilled release safeguards; no approval recorded")
            return 2
        # External human governance decisions remain separate even if
        # these technical preconditions are eventually fulfilled.
        print("PASS: Sila review roster and main-branch protections are configured")
        print("NOTE: This is not a human approval, merge, activation, or publication")
        return 0
    except (ClosureError, ReviewError, OSError, KeyError, TypeError) as error:
        print("SILA CLOSURE BLOCKED:", error, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
