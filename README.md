# contributions-text

Paints a text message on your GitHub contribution graph by generating a large
number of backdated commits on a dedicated branch. A weekly GitHub Actions
workflow wipes and recreates that branch so the message tracks the rolling
year window at high green intensity (capped at 50 commits per square).

Default message: `HELLO WORLD!`

## How it works

1. A 5-row bitmap font renders the message; it is placed with a 1-row
   empty margin on Sunday and Saturday inside GitHub's 7-row week
   (Monday–Friday). Most glyphs are 3 columns wide; `W` and `M` are 5
   columns wide, with 1 empty column between glyphs.
2. The message is centered horizontally inside the current 53-column
   rolling year window.
3. Every painted pixel is mapped to a concrete calendar date.
4. The script queries your GraphQL contribution calendar and finds
   `max_day` = highest daily contribution count in the last year.
5. For each painted date it makes `min(50, max(1, 2 * max_day))` backdated
   empty commits so the cell shows at high green intensity (capped at 50
   commits per square).
6. Each run switches the repo default branch to `master`, deletes and
   recreates `message` by branching from `master`, adds the painted
   commits on top, force-pushes it, then switches the default branch back
   to `message`.

## One-time setup

1. Push this repository to GitHub as a **public** repo. Keep the script on
   `master` (the workflow checks out `ref: master`).
2. Keep `master` as the branch that holds this script. After the first
   successful workflow run, the script will set the **default branch to
   `message`** automatically (and flip it back to `master` each run before
   deleting `message`). GitHub only counts commits toward your contribution
   graph if they land on the default branch (or `gh-pages`).
3. Create a Personal Access Token that can (a) read your contribution
   calendar via GraphQL, (b) force-push, and (c) change the default branch:
   - Classic PAT with the `repo` scope, **or**
   - Fine-grained PAT scoped to this repo with `contents: read/write`,
     `administration: read/write` (needed to change the default branch), and
     account permission `read:user`.
   Save it as the repo secret `MESSAGE_PAT`.
4. Add two more repo secrets used as commit author info:
   - `COMMIT_NAME` – any display name (e.g. your GitHub name).
   - `COMMIT_EMAIL` – **must** be an email verified on your GitHub account,
     otherwise the commits won't be attributed to you and won't count.
5. (Optional) Trigger the workflow manually once via
   Actions → *Weekly message* → *Run workflow* to paint immediately instead
   of waiting for the Sunday 06:00 UTC cron.

## Running locally

```bash
pip install -r requirements.txt

export MESSAGE_PAT=ghp_xxx
export GIT_AUTHOR_NAME="Your Name"
export GIT_AUTHOR_EMAIL="you@example.com"

# Preview without touching git:
python src/write_message.py --dry-run

# Skip the GraphQL call (useful offline) and force the intensity:
python src/write_message.py --dry-run --force-max 20

# Actually recreate and force-push the `message` branch:
python src/write_message.py
```

## Changing the message

Set the `MESSAGE` env var or pass `--message`:

```bash
MESSAGE="HI 2026" python src/write_message.py --dry-run
```

The font supports `A-Z`, `0-9`, and `! ? . , - :` (plus space). Lowercase
input is rendered with the uppercase glyphs. Total rendered width must fit
inside the 53-column year window; long messages will need to be shortened.

## Files

| Path | Purpose |
|------|---------|
| `src/font.py` | 5-row bitmap font (3-wide, or 5-wide for `M`/`W`). |
| `src/layout.py` | Renders a message (+ Sun/Sat margins) and maps pixels to dates. |
| `src/github_stats.py` | GraphQL max-daily fetch + default-branch switching. |
| `src/write_message.py` | CLI: flips default → recreates branch → flips default back. |
| `.github/workflows/daily-message.yml` | Weekly Sunday cron + `workflow_dispatch`. |
| `requirements.txt` | Python dependencies (stdlib only today). |

## Caveats

- The painted `message` branch history is rebuilt from scratch every day.
  Don't put real code on that branch; keep the script on `master`.
- GitHub sometimes takes several minutes to recompute the contribution
  graph after a push.
- If the weekly cron misses a run (e.g. Actions outage), the message will
  still be correct on the next successful run because the branch is
  rebuilt from scratch each time.
