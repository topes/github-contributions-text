"""Fetch the authenticated user's max daily contribution count from GitHub's
GraphQL API.

Uses `viewer` so the query works with whatever PAT is provided, without
needing the username configured separately.
"""

from __future__ import annotations

import json
import urllib.request
import urllib.error

GRAPHQL_URL = "https://api.github.com/graphql"

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


def fetch_max_daily_contributions(token: str) -> int:
    """Return the highest `contributionCount` across the last-year calendar."""
    body = json.dumps({"query": _QUERY}).encode("utf-8")
    req = urllib.request.Request(
        GRAPHQL_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "contributions-text-script",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"GitHub GraphQL request failed: {e.code} {e.reason}\n{e.read().decode('utf-8', 'replace')}") from e

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
