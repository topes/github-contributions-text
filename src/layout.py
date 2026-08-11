"""Map a rendered message onto concrete calendar dates within the current
rolling GitHub contribution year.

GitHub's contribution graph is laid out as columns of weeks (Sunday at the
top row, Saturday at the bottom). Glyphs are 5 rows tall and sit with a
1-row empty margin on Sunday and Saturday (Monday–Friday).
"""

from __future__ import annotations

from datetime import date, timedelta

from font import GLYPH_HEIGHT, VERTICAL_MARGIN, message_width, render_message

CALENDAR_ROWS = 7  # Sun → Sat
CALENDAR_COLUMNS = 53  # ~52 full past weeks plus the current partial week


def _current_week_sunday(today: date) -> date:
    """Return the Sunday on or before `today`."""
    # Python: Monday=0, Sunday=6. Days since Sunday: (weekday()+1) % 7.
    days_since_sunday = (today.weekday() + 1) % 7
    return today - timedelta(days=days_since_sunday)


def calendar_window(today: date) -> tuple[date, date]:
    """Return (start_sunday, end_saturday) for the visible calendar."""
    current_sun = _current_week_sunday(today)
    # 53 columns total: 52 weeks back + current week.
    start_sunday = current_sun - timedelta(weeks=CALENDAR_COLUMNS - 1)
    end_saturday = current_sun + timedelta(days=6)
    return start_sunday, end_saturday


def compute_pixel_dates(message: str, today: date) -> list[date]:
    """Render `message` centered on the current-year calendar and return the
    list of dates (<= today) that should be painted.

    Future dates in the current week are excluded so we don't try to backdate
    into the future.
    """
    rows = render_message(message)
    width = message_width(message)
    if width == 0:
        return []
    if width > CALENDAR_COLUMNS:
        raise ValueError(
            f"Message width {width} exceeds calendar width {CALENDAR_COLUMNS}. "
            "Shorten the message."
        )

    left_pad = (CALENDAR_COLUMNS - width) // 2
    start_sunday, _ = calendar_window(today)

    dates: set[date] = set()
    for glyph_row, row in enumerate(rows):
        calendar_row = VERTICAL_MARGIN + glyph_row
        for glyph_col, cell in enumerate(row):
            if cell != "X":
                continue
            col = left_pad + glyph_col
            day = start_sunday + timedelta(days=col * 7 + calendar_row)
            if day > today:
                continue
            dates.add(day)
    return sorted(dates)


def preview_grid(message: str, today: date) -> str:
    """Return a printable 7-row grid showing painted cells inside the
    calendar window. Useful for `--dry-run` output.
    """
    rows = render_message(message)
    width = message_width(message)
    left_pad = (CALENDAR_COLUMNS - width) // 2
    grid = [["." for _ in range(CALENDAR_COLUMNS)] for _ in range(CALENDAR_ROWS)]

    start_sunday, _ = calendar_window(today)
    for glyph_row, row in enumerate(rows):
        calendar_row = VERTICAL_MARGIN + glyph_row
        for glyph_col, cell in enumerate(row):
            if cell != "X":
                continue
            col = left_pad + glyph_col
            day = start_sunday + timedelta(days=col * 7 + calendar_row)
            marker = "X" if day <= today else "?"
            grid[calendar_row][col] = marker
    return "\n".join("".join(row) for row in grid)
