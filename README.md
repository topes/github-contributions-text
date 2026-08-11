# contributions-text

Paints a text message on your GitHub contribution graph by generating a large
number of backdated commits on a dedicated branch. A daily GitHub Actions
workflow wipes and recreates that branch so the message tracks the rolling
year window and always shows at the darkest green intensity.

Default message: `Hello!`

## How it works

1. A 7-row bitmap font renders the message into a `7 x N` grid (rows are
   Sunday → Saturday, columns are weeks). Most glyphs are 3 columns wide;
   `W` and `M` are 5 columns wide, with 1 empty column between glyphs.
2. The message is centered horizontally inside the current 53-column
   rolling year window.
3. Every painted pixel is mapped to a concrete calendar date.
4. The script queries your GraphQL contribution calendar and finds
   `max_day` = highest daily contribution count in the last year.
5. For each painted date it makes `max(1, 2 * max_day)` backdated empty
   commits so the cell always shows at the maximum green intensity (and
   stays at max even as your real activity grows).
6. The `message` branch is deleted and recreated as an orphan branch every
   run, then force-pushed.

## One-time setup

1. Push this repository to GitHub as a **public** repo. Keep the script on
   a branch called `source` (or edit `.github/workflows/daily-message.yml`
   to point at whatever branch holds the code).
2. Set the repository's **default branch to `message`**.
   Settings → Branches → Default branch → Switch. GitHub only counts commits
   toward your contribution graph if they land on the default branch (or
   `gh-pages`).
3. Create a Personal Access Token that can (a) read your contribution
   calendar via GraphQL and (b) force-push to this repo:
   - Classic PAT with the `repo` scope, **or**
   - Fine-grained PAT scoped to this repo with `contents: read/write` and
     account permission `read:user`.
   Save it as the repo secret `MESSAGE_PAT`.
4. Add two more repo secrets used as commit author info:
   - `COMMIT_NAME` – any display name (e.g. your GitHub name).
   - `COMMIT_EMAIL` – **must** be an email verified on your GitHub account,
     otherwise the commits won't be attributed to you and won't count.
5. (Optional) Trigger the workflow manually once via
   Actions → *Daily message* → *Run workflow* to paint immediately instead
   of waiting for the 06:00 UTC cron.

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
| `src/font.py` | 7-row bitmap font (3-wide, or 5-wide for `M`/`W`). |
| `src/layout.py` | Renders a message and maps painted pixels to dates. |
| `src/github_stats.py` | GraphQL query for max daily contributions. |
| `src/write_message.py` | CLI: recreates the branch, backdates commits, force-pushes. |
| `.github/workflows/daily-message.yml` | Daily cron + `workflow_dispatch`. |
| `requirements.txt` | Python dependencies (stdlib only today). |

## Caveats

- Force-pushing the default branch every day means the repo's history
  effectively resets daily. Don't use this on a repo that also hosts real
  code.
- GitHub sometimes takes several minutes to recompute the contribution
  graph after a push.
- If the daily cron misses a day (e.g. Actions outage), the message will
  still be correct on the next successful run because the branch is
  rebuilt from scratch each time.
