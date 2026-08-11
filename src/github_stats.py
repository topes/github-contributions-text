"""GitHub API helpers: contribution stats and default-branch switching."""

from __future__ import annotations

import json
import re
import subprocess
import urllib.error
import urllib.request

GRAPHQL_URL = "https://api.github.com/graphql"
REST_API = "https://api.github.com"

_QUERY = """
query {
  viewer {
    login
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            contributionCount
            date
          }
        }
      }
    }
  }
}
"""


def _request(
    method: str,
    url: str,
    token: str,
    body: dict | None = None,
) -> dict | None:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "contributions-text-script",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")
        raise RuntimeError(f"GitHub API {method} {url} failed: {e.code} {e.reason}\n{detail}") from e


def fetch_max_daily_contributions(token: str) -> int:
    """Return the highest `contributionCount` across the last-year calendar."""
    payload = _request("POST", GRAPHQL_URL, token, {"query": _QUERY})
    if not payload:
        raise RuntimeError("Empty GraphQL response")
    if "errors" in payload:
        raise RuntimeError(f"GraphQL errors: {payload['errors']}")

    weeks = (
        payload["data"]["viewer"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    )
    max_day = 0
    for week in weeks:
        for day in week["contributionDays"]:
            if day["contributionCount"] > max_day:
                max_day = day["contributionCount"]
    return max_day


def resolve_repo_slug(env_repo: str | None = None) -> str:
    """Return `owner/repo` from GITHUB_REPOSITORY or the `origin` remote URL."""
    if env_repo and "/" in env_repo:
        return env_repo

    result = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        check=True,
        capture_output=True,
        text=True,
    )
    url = result.stdout.strip()
    # https://github.com/owner/repo.git  or  git@github.com:owner/repo.git
    match = re.search(r"github\.com[:/](?P<slug>[^/]+/[^/]+?)(?:\.git)?$", url)
    if not match:
        raise RuntimeError(f"Could not parse owner/repo from origin URL: {url!r}")
    return match.group("slug")


def set_default_branch(token: str, repo_slug: str, branch: str) -> None:
    """PATCH the repository so `branch` becomes the default branch."""
    print(f"Setting default branch of {repo_slug} to {branch!r}")
    _request(
        "PATCH",
        f"{REST_API}/repos/{repo_slug}",
        token,
        {"default_branch": branch},
    )
