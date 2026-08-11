"""5-row bitmap font for the GitHub contributions grid.

Glyphs are 5 rows tall and are placed with a 1-row empty margin above and
below inside GitHub's 7-row week (Sunday → Saturday), so they occupy
Monday–Friday.

`X` = painted pixel, `.` = empty pixel.

Most glyphs are 3 columns wide. `W` and `M` are 5 columns wide.
Lookups are case-insensitive: lowercase input falls back to uppercase.
"""

from __future__ import annotations

GLYPH_HEIGHT = 5

# Empty rows above/below the glyph inside the 7-day calendar column.
VERTICAL_MARGIN = 1

# Inter-character spacing (empty columns between glyphs).
LETTER_SPACING = 1


_RAW_GLYPHS: dict[str, list[str]] = {
    " ": [
        "...",
        "...",
        "...",
        "...",
        "...",
    ],
    "A": [
        ".X.",
        "X.X",
        "XXX",
        "X.X",
        "X.X",
    ],
    "B": [
        "XX.",
        "X.X",
        "XX.",
        "X.X",
        "XX.",
    ],
    "C": [
        ".XX",
        "X..",
        "X..",
        "X..",
        ".XX",
    ],
    "D": [
        "XX.",
        "X.X",
        "X.X",
        "X.X",
        "XX.",
    ],
    "E": [
        "XXX",
        "X..",
        "XX.",
        "X..",
        "XXX",
    ],
    "F": [
        "XXX",
        "X..",
        "XX.",
        "X..",
        "X..",
    ],
    "G": [
        ".XX",
        "X..",
        "X.X",
        "X.X",
        ".XX",
    ],
    "H": [
        "X.X",
        "X.X",
        "XXX",
        "X.X",
        "X.X",
    ],
    "I": [
        "XXX",
        ".X.",
        ".X.",
        ".X.",
        "XXX",
    ],
    "J": [
        "XXX",
        "..X",
        "..X",
        "X.X",
        ".X.",
    ],
    "K": [
        "X.X",
        "XX.",
        "X..",
        "XX.",
        "X.X",
    ],
    "L": [
        "X..",
        "X..",
        "X..",
        "X..",
        "XXX",
    ],
    "M": [
        "X...X",
        "XX.XX",
        "X.X.X",
        "X...X",
        "X...X",
    ],
    "N": [
        "X.X",
        "XXX",
        "XXX",
        "X.X",
        "X.X",
    ],
    "O": [
        ".X.",
        "X.X",
        "X.X",
        "X.X",
        ".X.",
    ],
    "P": [
        "XX.",
        "X.X",
        "XX.",
        "X..",
        "X..",
    ],
    "Q": [
        ".X.",
        "X.X",
        "X.X",
        "XXX",
        ".XX",
    ],
    "R": [
        "XX.",
        "X.X",
        "XX.",
        "X.X",
        "X.X",
    ],
    "S": [
        ".XX",
        "X..",
        ".X.",
        "..X",
        "XX.",
    ],
    "T": [
        "XXX",
        ".X.",
        ".X.",
        ".X.",
        ".X.",
    ],
    "U": [
        "X.X",
        "X.X",
        "X.X",
        "X.X",
        ".X.",
    ],
    "V": [
        "X.X",
        "X.X",
        "X.X",
        ".X.",
        ".X.",
    ],
    "W": [
        "X...X",
        "X...X",
        "X.X.X",
        "XX.XX",
        "X...X",
    ],
    "X": [
        "X.X",
        "X.X",
        ".X.",
        "X.X",
        "X.X",
    ],
    "Y": [
        "X.X",
        "X.X",
        ".X.",
        ".X.",
        ".X.",
    ],
    "Z": [
        "XXX",
        "..X",
        ".X.",
        "X..",
        "XXX",
    ],
    "0": [
        ".X.",
        "X.X",
        "X.X",
        "X.X",
        ".X.",
    ],
    "1": [
        ".X.",
        "XX.",
        ".X.",
        ".X.",
        "XXX",
    ],
    "2": [
        "XX.",
        "..X",
        ".X.",
        "X..",
        "XXX",
    ],
    "3": [
        "XX.",
        "..X",
        ".X.",
        "..X",
        "XX.",
    ],
    "4": [
        "X.X",
        "X.X",
        "XXX",
        "..X",
        "..X",
    ],
    "5": [
        "XXX",
        "X..",
        "XX.",
        "..X",
        "XX.",
    ],
    "6": [
        ".XX",
        "X..",
        "XX.",
        "X.X",
        ".X.",
    ],
    "7": [
        "XXX",
        "..X",
        ".X.",
        ".X.",
        "X..",
    ],
    "8": [
        ".X.",
        "X.X",
        ".X.",
        "X.X",
        ".X.",
    ],
    "9": [
        ".X.",
        "X.X",
        ".XX",
        "..X",
        "XX.",
    ],
    "!": [
        ".X.",
        ".X.",
        ".X.",
        "...",
        ".X.",
    ],
    "?": [
        "XX.",
        "..X",
        ".X.",
        "...",
        ".X.",
    ],
    ".": [
        "...",
        "...",
        "...",
        "...",
        ".X.",
    ],
    ",": [
        "...",
        "...",
        "...",
        ".X.",
        "X..",
    ],
    "-": [
        "...",
        "...",
        "XXX",
        "...",
        "...",
    ],
    ":": [
        "...",
        ".X.",
        "...",
        ".X.",
        "...",
    ],
}


def _validate() -> None:
    for char, rows in _RAW_GLYPHS.items():
        assert len(rows) == GLYPH_HEIGHT, f"glyph {char!r} must have {GLYPH_HEIGHT} rows"
        widths = {len(r) for r in rows}
        assert len(widths) == 1, f"glyph {char!r} has inconsistent widths: {widths}"
        w = widths.pop()
        if char in {"M", "W"}:
            assert w == 5, f"glyph {char!r} must be 5 columns"
        elif char == " ":
            assert w == 3
        else:
            assert w == 3, f"glyph {char!r} must be 3 columns (got {w})"


_validate()


def get_glyph(char: str) -> list[str]:
    """Return the bitmap rows for `char`. Case-insensitive; missing glyphs raise KeyError."""
    if char in _RAW_GLYPHS:
        return _RAW_GLYPHS[char]
    upper = char.upper()
    if upper in _RAW_GLYPHS:
        return _RAW_GLYPHS[upper]
    raise KeyError(f"No glyph for character {char!r}")


def glyph_width(char: str) -> int:
    return len(get_glyph(char)[0])


def render_message(message: str) -> list[str]:
    """Render `message` as a list of GLYPH_HEIGHT rows of `X`/`.` characters.

    Glyphs are joined left-to-right with `LETTER_SPACING` empty columns between
    them. Vertical calendar margins are applied by the layout module.
    """
    if not message:
        return ["" for _ in range(GLYPH_HEIGHT)]

    rows = ["" for _ in range(GLYPH_HEIGHT)]
    for i, ch in enumerate(message):
        glyph = get_glyph(ch)
        for r in range(GLYPH_HEIGHT):
            if i > 0:
                rows[r] += "." * LETTER_SPACING
            rows[r] += glyph[r]
    return rows


def message_width(message: str) -> int:
    if not message:
        return 0
    return sum(glyph_width(c) for c in message) + LETTER_SPACING * (len(message) - 1)
