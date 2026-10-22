#!/usr/bin/env python3
"""Check every link in the SIP documents.

Relative links and anchors are resolved on disk. Links to files on GitHub are
fetched from raw.githubusercontent.com at the pinned commit. Links to GitHub
repository pages are checked with `git ls-remote`. Everything else is fetched
with curl. Code fences are skipped, since they hold examples and regular
expressions rather than links.
"""

import concurrent.futures
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = ["README.md", "SIPS/sip-1.md", "sip-template.md"]
# The template is copied into SIPS/ before use, so its relative links resolve from there.
BASE_DIR = {"sip-template.md": "SIPS"}


def slug(heading):
    return re.sub(r"[^a-z0-9 -]", "", heading.lower().strip()).replace(" ", "-")


def curl(url):
    out = subprocess.run(
        ["curl", "-sS", "-o", "/dev/null", "-w", "%{http_code}", "-m", "20", "-L", "-A", "Mozilla/5.0", url],
        capture_output=True,
        text=True,
    ).stdout
    return out or "timeout"


def check(item):
    path, url = item
    base = os.path.join(ROOT, BASE_DIR.get(path, os.path.dirname(path)))
    if not url.startswith("http"):
        target, _, anchor = url.partition("#")
        full = os.path.normpath(os.path.join(base, target)) if target else os.path.join(ROOT, path)
        if not os.path.exists(full):
            return "MISSING", path, url
        if anchor:
            with open(full) as f:
                headings = [slug(h) for h in re.findall(r"^#+ (.*)$", f.read(), re.M)]
            if anchor not in headings:
                return "BROKEN-ANCHOR", path, url
        return "OK", path, url
    m = re.match(r"https://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.*)", url)
    if m:
        owner, repo, ref, file = m.groups()
        code = curl(f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{file}")
        return ("OK" if code == "200" else f"HTTP-{code}"), path, url
    m = re.match(r"https://github\.com/([^/]+)/([^/#]+)/?(.*)$", url)
    if m:
        owner, repo, rest = m.groups()
        rc = subprocess.run(
            ["git", "ls-remote", "--exit-code", f"https://github.com/{owner}/{repo}", "HEAD"],
            capture_output=True,
            timeout=60,
        ).returncode
        if rc != 0:
            return "REPO-MISSING", path, url
        return ("OK (repository exists; page not fetched)" if rest else "OK"), path, url
    code = curl(url)
    return ("OK" if code == "200" else f"HTTP-{code}"), path, url


def main():
    links = set()
    for path in FILES:
        with open(os.path.join(ROOT, path)) as f:
            text = re.sub(r"```.*?```", "", f.read(), flags=re.S)
        links.update((path, u) for u in re.findall(r"\]\(([^)\s]+)\)", text))
        links.update((path, u) for u in re.findall(r"<(https?://[^>]+)>", text))
    with concurrent.futures.ThreadPoolExecutor(16) as pool:
        results = sorted(pool.map(check, sorted(links)), key=lambda r: (r[0].startswith("OK"), r[1], r[2]))
    for status, path, url in results:
        print(f"{status}  {path}  {url}")
    bad = [r for r in results if not r[0].startswith("OK")]
    print(f"links: {len(results)} checked, {len(bad)} broken")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
