#!/usr/bin/env python3
"""Paint a message on the GitHub contribution graph.

Recreates a dedicated branch (default: `message`) from `master`, then creates
backdated empty commits on each date that corresponds to a painted pixel in
the message. The number of commits per painted day is
`max(1, 2 * max_daily_contributions_last_year)` so the message always shows
at the maximum green intensity.

Before deleting `message`, the repo default branch is switched to `master`
(so GitHub allows the delete). After the branch is recreated and pushed, the
default is switched back to `message`.

Environment variables:
  MESSAGE_PAT / GH_TOKEN / GITHUB_TOKEN  GitHub token for GraphQL + push
  GIT_AUTHOR_NAME                        Commit author name
  GIT_AUTHOR_EMAIL                       Commit author email (GitHub-verified)
  MESSAGE                                Text to paint (default: "HELLO WORLD!")
  BRANCH                                 Branch to (re)create (default: "message")
  SCRIPT_BRANCH                          Safe default while recreating (default: "master")
  REMOTE                                 Git remote to push to (default: "origin")
  GITHUB_REPOSITORY                      Optional owner/repo override
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import date

# Allow running as `python src/write_message.py` from repo root.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from github_stats import (
    fetch_max_daily_contributions,
    resolve_repo_slug,
    set_default_branch,
)
from layout import compute_pixel_dates, preview_grid


def _run(cmd: list[str], *, env: dict | None = None, check: bool = True, capture: bool = False) -> subprocess.CompletedProcess:
    print("$ " + " ".join(cmd))
    result = subprocess.run(cmd, env=env, check=check, capture_output=capture, text=True)
    if capture and result.stdout:
        print(result.stdout.rstrip())
    return result


def _get_token() -> str:
    for name in ("MESSAGE_PAT", "GH_TOKEN", "GITHUB_TOKEN"):
        val = os.environ.get(name)
        if val:
            return val
    raise SystemExit("No token found. Set MESSAGE_PAT (preferred), GH_TOKEN, or GITHUB_TOKEN.")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--message", default=os.environ.get("MESSAGE", "HELLO WORLD!"))
    p.add_argument("--branch", default=os.environ.get("BRANCH", "message"))
    p.add_argument(
        "--script-branch",
        default=os.environ.get("SCRIPT_BRANCH", "master"),
        help="Branch to base `message` on, and to use as default while recreating (default: master).",
    )
    p.add_argument("--remote", default=os.environ.get("REMOTE", "origin"))
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the pixel dates and commit counts, don't touch git.",
    )
    p.add_argument(
        "--force-max",
        type=int,
        default=None,
        help="Skip the GraphQL call and use this integer as max_daily_contributions.",
    )
    return p.parse_args(argv)


def recreate_branch_from_script(
    branch: str,
    script_branch: str,
    remote: str,
    author_name: str,
    author_email: str,
) -> None:
    """Delete local `branch` and recreate it from `script_branch` (e.g. master)."""
    _run(["git", "config", "user.name", author_name])
    _run(["git", "config", "user.email", author_email])

    # Ensure we have the latest script branch tip to branch from.
    _run(["git", "fetch", remote, script_branch])
    _run(["git", "checkout", script_branch])
    # Align with remote tip when available (no-op failure is fine locally).
    subprocess.run(
        ["git", "reset", "--hard", f"{remote}/{script_branch}"],
        check=False,
    )

    subprocess.run(["git", "branch", "-D", branch], check=False)
    _run(["git", "checkout", "-B", branch, script_branch])


def make_pixel_commits(dates: list[date], commits_per_day: int, env: dict) -> None:
    """Create `commits_per_day` empty commits on each date in `dates`."""
    for d in dates:
        for i in range(commits_per_day):
            # Spread within the day so timestamps are distinct.
            hh = 12
            mm = (i * 3) % 60
            ss = (i * 7) % 60
            ts = f"{d.isoformat()}T{hh:02d}:{mm:02d}:{ss:02d}"
            step_env = dict(env)
            step_env["GIT_AUTHOR_DATE"] = ts
            step_env["GIT_COMMITTER_DATE"] = ts
            _run(
                [
                    "git",
                    "commit",
                    "--allow-empty",
                    "-m",
                    f"pixel {d.isoformat()} #{i + 1}",
                ],
                env=step_env,
            )


def delete_and_force_push(remote: str, branch: str) -> None:
    # Default branch must already be something else (e.g. master).
    subprocess.run(["git", "push", remote, "--delete", branch], check=False)
    _run(["git", "push", remote, branch, "--force"])


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    author_name = os.environ.get("GIT_AUTHOR_NAME") or os.environ.get("GITHUB_ACTOR")
    author_email = os.environ.get("GIT_AUTHOR_EMAIL")
    if not args.dry_run:
        if not author_name:
            raise SystemExit("Set GIT_AUTHOR_NAME (or GITHUB_ACTOR in Actions).")
        if not author_email:
            raise SystemExit("Set GIT_AUTHOR_EMAIL to a GitHub-verified email.")

    today = date.today()
    dates = compute_pixel_dates(args.message, today)
    print(f"Message: {args.message!r}")
    print(f"Pixel-dates: {len(dates)} (window ends {today.isoformat()})")
    print("Preview (X = will paint, ? = future cell skipped; Sun/Sat margins empty):")
    print(preview_grid(args.message, today))
    print()

    if args.force_max is not None:
        max_day = args.force_max
        print(f"Using forced max_daily_contributions = {max_day}")
        token = None
    else:
        token = _get_token()
        max_day = fetch_max_daily_contributions(token)
        print(f"GraphQL: max_daily_contributions = {max_day}")

    # Double the current max intensity, but never more than 50 commits per square.
    commits_per_day = min(50, max(1, max_day * 2))
    total_commits = commits_per_day * len(dates)
    print(f"commits_per_painted_day = {commits_per_day}  (total commits = {total_commits})")

    if args.dry_run:
        print()
        print("Dry run; skipping git.")
        for d in dates:
            print(f"  {d.isoformat()}  x{commits_per_day}")
        return 0

    if not dates:
        print("No painted dates; nothing to do.")
        return 0

    if token is None:
        token = _get_token()

    repo_slug = resolve_repo_slug(os.environ.get("GITHUB_REPOSITORY"))

    # Cannot delete the default branch — move default to master first.
    set_default_branch(token, repo_slug, args.script_branch)

    recreate_branch_from_script(
        args.branch,
        args.script_branch,
        args.remote,
        author_name,
        author_email,
    )

    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = author_name
    env["GIT_COMMITTER_NAME"] = author_name
    env["GIT_AUTHOR_EMAIL"] = author_email
    env["GIT_COMMITTER_EMAIL"] = author_email

    make_pixel_commits(dates, commits_per_day, env)
    delete_and_force_push(args.remote, args.branch)

    # Point contributions back at the painted branch.
    set_default_branch(token, repo_slug, args.branch)

    print()
    print(f"Done. Painted {len(dates)} days x {commits_per_day} commits on '{args.branch}'.")
    print(f"Default branch restored to '{args.branch}'.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
