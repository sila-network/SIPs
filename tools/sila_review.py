#!/usr/bin/env python3
"""Read-only, fail-closed pull-request review gate for Sila Network.

The bot never approves, merges, posts comments, assigns people, or changes
governance state. It checks real GitHub review decisions against an explicitly
authorized Sila reviewer roster. Unassigned roles block the applicable PR.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys
import tomllib
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
POLICY_FILE = Path("config/sila-review.toml")
GITHUB_HOST = "https://api.github.com"
ROLES = frozenset(("editor", "technical"))
LOGIN = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?\Z")
HEX_SHA = re.compile(r"[a-fA-F0-9]{40}\Z")


class ReviewError(ValueError):
    """Required information, authorization, or external verification is missing."""


def load_policy(path: Path = ROOT / POLICY_FILE) -> dict:
    """Read a minimal trusted policy. Empty review rosters are explicitly allowed."""
    with path.open("rb") as stream:
        policy = tomllib.load(stream)
    if set(policy) != {"review", "reviewers"}:
        raise ReviewError("Sila review policy has unknown or missing sections")
    review, reviewers = policy["review"], policy["reviewers"]
    expected = {"repository", "spec_roles", "code_roles", "content_roles"}
    if set(review) != expected or set(reviewers) != ROLES:
        raise ReviewError("Sila reviewer policy has unknown or missing fields")
    if review["repository"] != "sila-network/SIPs":
        raise ReviewError("review policy points outside the official Sila repository")
    for key in ("spec_roles", "code_roles", "content_roles"):
        roles = review[key]
        if not isinstance(roles, list) or not roles or any(r not in ROLES for r in roles):
            raise ReviewError("Sila required review roles are invalid")
        if len(roles) != len(set(roles)):
            raise ReviewError("Sila review roles are duplicated")
    for role, logins in reviewers.items():
        if not isinstance(logins, list):
            raise ReviewError(f"invalid reviewer roster: {role}")
        normalized = []
        for login in logins:
            if not isinstance(login, str) or not LOGIN.fullmatch(login):
                raise ReviewError(f"invalid GitHub reviewer login in {role}")
            normalized.append(login.casefold())
        if len(normalized) != len(set(normalized)):
            raise ReviewError(f"duplicate Sila reviewer in {role}")
    return policy


def canonical_path(raw: str) -> str:
    if not isinstance(raw, str) or not raw or raw.startswith("/") or "\\" in raw:
        raise ReviewError("invalid proposed file path")
    parts = raw.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise ReviewError("noncanonical proposed file path")
    if any(ord(ch) < 32 for ch in raw):
        raise ReviewError("control character in proposed path")
    return raw


def classify_changes(changes: list[dict], policy: dict) -> tuple[set[str], bool, list[str]]:
    """Use actual GitHub changed-file records; renames cover both old and new names."""
    if not isinstance(changes, list) or not changes:
        raise ReviewError("changed-file listing was unavailable or empty")
    requested: set[str] = set()
    protected_policy = False
    paths: set[str] = set()
    for change in changes:
        if not isinstance(change, dict) or not isinstance(change.get("filename"), str):
            raise ReviewError("malformed changed-file record")
        candidates = [change["filename"]]
        if change.get("status") == "renamed":
            if not isinstance(change.get("previous_filename"), str):
                raise ReviewError("renamed change has no original file path")
            candidates.append(change["previous_filename"])
        for original in candidates:
            path = canonical_path(original)
            paths.add(path)
            if path == POLICY_FILE.as_posix():
                protected_policy = True
            if path.startswith("SIPS/") or path == "sip-template.md":
                requested.update(policy["review"]["spec_roles"])
            elif path.startswith(("tools/", "tests/", ".github/")) or path.startswith("config/"):
                requested.update(policy["review"]["code_roles"])
            else:
                requested.update(policy["review"]["content_roles"])
    if not requested:
        raise ReviewError("no Sila review class was identified")
    return requested, protected_policy, sorted(paths)


def approved_reviewers(
    reviews: list[dict], head_sha: str, pr_author: str
) -> set[str]:
    """Only a real, current-head APPROVED review counts; dismissal overrides it."""
    if not HEX_SHA.fullmatch(head_sha):
        raise ReviewError("unverifiable pull-request head commit")
    if not isinstance(reviews, list) or any(not isinstance(item, dict) for item in reviews):
        raise ReviewError("malformed GitHub review listing")
    current: dict[str, dict] = {}
    for review in sorted(reviews, key=lambda v: (str(v.get("submitted_at") or ""), int(v.get("id") or 0))):
        if not isinstance(review, dict) or not isinstance(review.get("user"), dict):
            raise ReviewError("invalid GitHub review record")
        login = review["user"].get("login")
        if not isinstance(login, str) or not LOGIN.fullmatch(login):
            raise ReviewError("invalid reviewer identity")
        state = review.get("state")
        if state in ("APPROVED", "CHANGES_REQUESTED", "DISMISSED"):
            current[login.casefold()] = review
    result: set[str] = set()
    for login, review in current.items():
        if login == pr_author.casefold():
            continue
        if review.get("state") == "APPROVED" and review.get("commit_id") == head_sha:
            result.add(login)
    return result


def require_reviews(
    policy: dict, roles: set[str], approved: set[str]
) -> tuple[bool, list[str]]:
    missing = []
    for role in sorted(roles):
        authorized = {login.casefold() for login in policy["reviewers"][role]}
        if not authorized:
            missing.append(f"{role}: no Sila reviewer has been authorized")
        elif not (authorized & approved):
            missing.append(f"{role}: missing current-head approval from an authorized reviewer")
    if missing:
        return False, missing
    # Different roles require different independent human approvals.
    candidates = [({login.casefold() for login in policy["reviewers"][role]} & approved)
                  for role in sorted(roles)]
    def distinct(index: int, selected: set[str]) -> bool:
        if index == len(candidates):
            return True
        return any(distinct(index + 1, selected | {login})
                   for login in candidates[index] if login not in selected)
    if not distinct(0, set()):
        return False, ["independent Sila review roles require distinct authorized accounts"]
    return True, []


def github_pages(repo: str, number: int, endpoint: str, token: str) -> list[dict]:
    if repo != "sila-network/SIPs" or not isinstance(number, int) or number < 1:
        raise ReviewError("invalid Sila pull-request target")
    if endpoint not in ("files", "reviews") or not token:
        raise ReviewError("unsupported review source or missing read token")
    output: list[dict] = []
    # A truncated listing would create a bypass. Always fail closed.
    for page in range(1, 51):
        url = f"{GITHUB_HOST}/repos/{repo}/pulls/{number}/{endpoint}?per_page=100&page={page}"
        request = Request(url, headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "sila-native-review",
        })
        try:
            with urlopen(request, timeout=18) as response:
                result = json.load(response)
        except (HTTPError, URLError, TimeoutError, ValueError) as error:
            raise ReviewError(f"could not verify Sila GitHub {endpoint} data") from error
        if not isinstance(result, list) or any(not isinstance(x, dict) for x in result):
            raise ReviewError(f"invalid Sila GitHub {endpoint} listing")
        output.extend(result)
        if len(result) < 100:
            return output
    raise ReviewError(f"GitHub {endpoint} listing exceeded safe verification limit")


def evaluate_pr(event: dict, policy: dict, token: str) -> tuple[bool, list[str]]:
    pr = event.get("pull_request")
    repository = event.get("repository")
    if not isinstance(pr, dict) or not isinstance(repository, dict):
        raise ReviewError("GitHub pull-request event is missing")
    target = repository.get("full_name")
    base = pr.get("base", {})
    head = pr.get("head", {})
    if target != policy["review"]["repository"] or not isinstance(base, dict) or not isinstance(head, dict):
        raise ReviewError("unexpected repository or pull-request metadata")
    if base.get("repo", {}).get("full_name") != target:
        raise ReviewError("pull request does not target the Sila repository")
    number = pr.get("number")
    if not isinstance(number, int) or number < 1:
        raise ReviewError("invalid pull-request number")
    pr_author = pr.get("user", {}).get("login")
    sha = head.get("sha")
    if not isinstance(pr_author, str) or not LOGIN.fullmatch(pr_author) or not isinstance(sha, str):
        raise ReviewError("pull-request author or revision is invalid")
    if pr.get("draft") is True:
        raise ReviewError("draft pull request is not ready for mandatory review")
    changed = github_pages(target, number, "files", token)
    roles, policy_changed, paths = classify_changes(changed, policy)
    print(f"Sila PR #{number}: {len(paths)} changed paths; required roles: {', '.join(sorted(roles))}")
    if policy_changed:
        return False, ["reviewer policy cannot authorize itself in the same pull request"]
    reviews = github_pages(target, number, "reviews", token)
    approved = approved_reviewers(reviews, sha, pr_author)
    return require_reviews(policy, roles, approved)


def main() -> int:
    parser = argparse.ArgumentParser(description="Sila-only, read-only review gate")
    parser.add_argument("command", choices=("policy", "pull-request"))
    parser.add_argument("--event", default=os.getenv("GITHUB_EVENT_PATH", ""))
    args = parser.parse_args()
    try:
        policy = load_policy()
        if args.command == "policy":
            print("PASS: Sila reviewer policy schema is valid; no governance appointment inferred")
            return 0
        if not args.event:
            raise ReviewError("missing trusted pull-request event file")
        with open(args.event, encoding="utf-8") as handle:
            event = json.load(handle)
        passed, blockers = evaluate_pr(event, policy, os.getenv("GITHUB_TOKEN", ""))
        if not passed:
            for blocker in blockers:
                print("REVIEW BLOCKED:", blocker, file=sys.stderr)
            return 2
        print("PASS: mandatory independent Sila reviews verified for current PR head")
        return 0
    except (ReviewError, OSError, ValueError, TypeError, KeyError) as error:
        print("REVIEW BLOCKED:", error, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
