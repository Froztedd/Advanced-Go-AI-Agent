"""Immutable Board representation for Go.

The Board is a frozen dataclass. Every state-changing operation returns a
new Board; nothing is ever mutated. Cells are stored as a flat tuple of
ints to keep copies cheap and the value hashable.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING

from go_arena.engine.types import PASS, Color, Move, Pass, Place, Position

if TYPE_CHECKING:
    pass


class IllegalMove(ValueError):
    """Raised when a move violates the rules."""


_NEIGHBOR_OFFSETS: tuple[tuple[int, int], ...] = ((-1, 0), (1, 0), (0, -1), (0, 1))


@dataclass(frozen=True, slots=True)
class Board:
    """Immutable Go board state.

    Attributes:
        size: Edge length of the (square) board.
        cells: Flat row-major tuple of length ``size * size``. Each entry
            is the integer value of a :class:`Color`.
        ko_history: Frozen set of position hashes that have already
            occurred in this game. Used to enforce positional superko.
        previous_cells: Cell tuple from the position immediately before
            the most recent move. Used by simple-ko mode to mirror the
            legacy CSCI 561 host: a capturing move that re-creates the
            single previous position is illegal.
        consecutive_passes: Number of passes played in a row immediately
            preceding this position.
        move_number: Total number of moves played to reach this state
            (including passes).
        simple_ko_mode: When True, ko checks use the legacy "simple ko"
            rule (compare cells to ``previous_cells`` only). When False
            (default), positional superko is enforced via ``ko_history``.
    """

    size: int
    cells: tuple[int, ...]
    ko_history: frozenset[int] = field(default_factory=frozenset)
    previous_cells: tuple[int, ...] | None = None
    consecutive_passes: int = 0
    move_number: int = 0
    simple_ko_mode: bool = False

    @classmethod
    def empty(cls, size: int = 5, *, simple_ko_mode: bool = False) -> Board:
        """Construct an empty board of the given size."""
        return cls(
            size=size,
            cells=tuple([Color.EMPTY.value] * (size * size)),
            simple_ko_mode=simple_ko_mode,
        )

    def index(self, row: int, col: int) -> int:
        """Return the flat cell index for ``(row, col)``."""
        return row * self.size + col

    def in_bounds(self, row: int, col: int) -> bool:
        """Return True if ``(row, col)`` lies on the board."""
        return 0 <= row < self.size and 0 <= col < self.size

    def at(self, row: int, col: int) -> Color:
        """Return the :class:`Color` at ``(row, col)``."""
        return Color(self.cells[self.index(row, col)])

    def positions(self) -> Iterator[Position]:
        """Iterate over every position on the board, row-major."""
        for r in range(self.size):
            for c in range(self.size):
                yield (r, c)

    def neighbors(self, row: int, col: int) -> Iterator[Position]:
        """Yield in-bounds 4-connected neighbors of ``(row, col)``."""
        for dr, dc in _NEIGHBOR_OFFSETS:
            nr, nc = row + dr, col + dc
            if 0 <= nr < self.size and 0 <= nc < self.size:
                yield (nr, nc)

    def group_at(self, pos: Position) -> frozenset[Position]:
        """Return the connected same-color group containing ``pos``.

        Returns an empty set if the cell at ``pos`` is empty.
        """
        target = self.cells[self.index(*pos)]
        if target == Color.EMPTY.value:
            return frozenset()
        seen: set[Position] = set()
        stack: list[Position] = [pos]
        while stack:
            p = stack.pop()
            if p in seen:
                continue
            seen.add(p)
            for n in self.neighbors(*p):
                if n not in seen and self.cells[self.index(*n)] == target:
                    stack.append(n)
        return frozenset(seen)

    def liberties_of(self, pos: Position) -> frozenset[Position]:
        """Return the set of empty positions adjacent to the group at ``pos``."""
        group = self.group_at(pos)
        if not group:
            return frozenset()
        libs: set[Position] = set()
        for p in group:
            for n in self.neighbors(*p):
                if self.cells[self.index(*n)] == Color.EMPTY.value:
                    libs.add(n)
        return frozenset(libs)

    def _replace_cells(self, new_cells: tuple[int, ...], **kwargs: object) -> Board:
        return replace(self, cells=new_cells, **kwargs)  # type: ignore[arg-type]

    def with_stone(self, row: int, col: int, color: Color) -> Board:
        """Return a new Board with ``color`` placed at ``(row, col)``.

        Does not check legality, run captures, or update ko / move counters.
        Intended as a low-level building block for :mod:`go_arena.engine.rules`.
        """
        idx = self.index(row, col)
        cells = list(self.cells)
        cells[idx] = color.value
        return self._replace_cells(tuple(cells))

    def with_removed(self, positions: frozenset[Position]) -> Board:
        """Return a new Board with the given positions emptied."""
        if not positions:
            return self
        cells = list(self.cells)
        for r, c in positions:
            cells[self.index(r, c)] = Color.EMPTY.value
        return self._replace_cells(tuple(cells))

    def position_hash(self, color_to_play: Color) -> int:
        """Hash the position together with the side to move.

        Two positions with identical stone configuration but different
        sides to move hash differently. This is what positional superko
        is checked against.
        """
        return hash((self.cells, int(color_to_play)))

    def with_move(self, move: Move, color: Color) -> Board:
        """Return the board state after ``color`` plays ``move``.

        Importing :func:`go_arena.engine.rules.apply_move` here would
        create a cycle. Routing through the rules module is the public
        path; this method is a convenience that delegates to it.
        """
        from go_arena.engine.rules import apply_move

        return apply_move(self, move, color)

    def legal_moves(self, color: Color) -> list[Move]:
        """Return all legal moves for ``color``, including :data:`PASS`."""
        from go_arena.engine.rules import is_legal

        moves: list[Move] = [PASS]
        for r, c in self.positions():
            if self.cells[self.index(r, c)] != Color.EMPTY.value:
                continue
            place = Place(r, c)
            if is_legal(self, place, color):
                moves.append(place)
        return moves

    @property
    def is_terminal(self) -> bool:
        """True when two passes have been played consecutively."""
        return self.consecutive_passes >= 2

    def __str__(self) -> str:
        rows = []
        for r in range(self.size):
            row_chars = []
            for c in range(self.size):
                v = self.cells[self.index(r, c)]
                row_chars.append({0: ".", 1: "X", 2: "O"}[v])
            rows.append(" ".join(row_chars))
        return "\n".join(rows)


__all__ = ["PASS", "Board", "Color", "IllegalMove", "Move", "Pass", "Place"]
