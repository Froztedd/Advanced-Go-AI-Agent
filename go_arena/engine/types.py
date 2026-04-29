"""Core types for the Go engine: Color, Move, Position."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Final

Position = tuple[int, int]


class Color(IntEnum):
    """Stone color. Integer values match the legacy CSCI 561 encoding."""

    EMPTY = 0
    BLACK = 1
    WHITE = 2

    @property
    def opponent(self) -> Color:
        """Return the opposing color. Raises if called on EMPTY."""
        if self is Color.BLACK:
            return Color.WHITE
        if self is Color.WHITE:
            return Color.BLACK
        raise ValueError("EMPTY has no opponent")


@dataclass(frozen=True, slots=True)
class Pass:
    """The pass move."""

    def __repr__(self) -> str:
        return "Pass"


@dataclass(frozen=True, slots=True)
class Place:
    """A stone placement at (row, col)."""

    row: int
    col: int

    def __repr__(self) -> str:
        return f"Place({self.row}, {self.col})"


Move = Pass | Place

PASS: Final[Pass] = Pass()


def parse_move(text: str) -> Move:
    """Parse a move from CLI / text form.

    Accepts ``"PASS"``, ``"pass"``, ``"r,c"``, or ``"r c"``.
    """
    text = text.strip()
    if text.upper() == "PASS":
        return PASS
    sep = "," if "," in text else " "
    row_str, _, col_str = text.partition(sep)
    return Place(int(row_str), int(col_str))
