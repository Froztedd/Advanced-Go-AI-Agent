"""ASCII rendering for boards."""

from __future__ import annotations

from go_arena.engine.board import Board
from go_arena.engine.types import Color

_GLYPHS: dict[int, str] = {
    Color.EMPTY.value: ".",
    Color.BLACK.value: "X",
    Color.WHITE.value: "O",
}

_COL_LETTERS = "ABCDEFGHJKLMNOPQRST"  # Skip 'I' as in standard Go notation.


def render_ascii(board: Board) -> str:
    """Return a multi-line ASCII rendering of ``board`` with column letters
    and 1-indexed row numbers (top row is row 1).
    """
    size = board.size
    header = "   " + " ".join(_COL_LETTERS[c] for c in range(size))
    lines = [header]
    for r in range(size):
        cells = " ".join(_GLYPHS[board.cells[board.index(r, c)]] for c in range(size))
        lines.append(f"{r + 1:>2} {cells}")
    return "\n".join(lines)


__all__ = ["render_ascii"]
