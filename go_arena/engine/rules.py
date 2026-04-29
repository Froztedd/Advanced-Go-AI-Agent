"""Go rules: legality, move application, scoring.

Two scoring functions are exported:

* :func:`score_area` is Chinese / Tromp-Taylor area scoring (stones + the
  empties strictly surrounded by one color, plus komi for white). This is
  the default everywhere in new code.
* :func:`score_stone_count` is the legacy CSCI 561 host scoring (stones
  only, plus komi for white). It exists for the regression test that
  proves we match the original ``host.py`` behavior.
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, TypedDict

from go_arena.engine.board import Board, IllegalMove
from go_arena.engine.types import Color, Move, Pass, Place, Position

if TYPE_CHECKING:
    pass


class ScoreReport(TypedDict):
    """Outcome of a scoring call."""

    black: float
    white: float
    winner: Color  # EMPTY signals a tie.


def _captured_groups(board: Board, color: Color) -> frozenset[Position]:
    """Return all stones of ``color`` that have zero liberties on ``board``."""
    seen: set[Position] = set()
    captured: set[Position] = set()
    for r, c in board.positions():
        if board.cells[board.index(r, c)] != color.value:
            continue
        if (r, c) in seen:
            continue
        group = board.group_at((r, c))
        seen.update(group)
        if not board.liberties_of((r, c)):
            captured.update(group)
    return frozenset(captured)


def _resolve_placement(board: Board, place: Place, color: Color) -> tuple[Board, int]:
    """Place ``color`` at ``place`` and resolve captures.

    Returns the resulting :class:`Board` and the number of opponent stones
    removed. Does not check legality; caller is responsible.
    """
    after_place = board.with_stone(place.row, place.col, color)
    enemy_dead = _captured_groups(after_place, color.opponent)
    after_capture = after_place.with_removed(enemy_dead)
    return after_capture, len(enemy_dead)


def is_legal(board: Board, move: Move, color: Color) -> bool:
    """Return True iff ``color`` may play ``move`` on ``board``.

    A pass is always legal. A placement is legal iff:

    1. The target cell is in bounds and empty.
    2. After placing, either the placed group has at least one liberty,
       or the placement captures one or more opponent stones.
    3. Ko: under the default positional superko rule, the resulting
       position has not been seen before in this game. Under
       ``board.simple_ko_mode`` (legacy CSCI 561 parity), only the
       single previous position counts, and only when the move captured.
    """
    if isinstance(move, Pass):
        return True

    if not board.in_bounds(move.row, move.col):
        return False
    if board.cells[board.index(move.row, move.col)] != Color.EMPTY.value:
        return False

    after_capture, captured = _resolve_placement(board, move, color)
    own_libs = after_capture.liberties_of((move.row, move.col))
    if not own_libs and captured == 0:
        return False  # suicide

    if board.simple_ko_mode:
        if (
            captured > 0
            and board.previous_cells is not None
            and after_capture.cells == board.previous_cells
        ):
            return False
    else:
        new_hash = after_capture.position_hash(color.opponent)
        if new_hash in board.ko_history:
            return False

    return True


def apply_move(board: Board, move: Move, color: Color) -> Board:
    """Return the board state after ``color`` plays ``move``.

    Raises :class:`IllegalMove` if the move is not legal under
    :func:`is_legal`.
    """
    if not is_legal(board, move, color):
        raise IllegalMove(f"Illegal move {move!r} for {color.name}")

    if isinstance(move, Pass):
        new_history = board.ko_history | {board.position_hash(color.opponent)}
        return replace(
            board,
            ko_history=new_history,
            previous_cells=board.cells,
            consecutive_passes=board.consecutive_passes + 1,
            move_number=board.move_number + 1,
        )

    after_capture, _ = _resolve_placement(board, move, color)
    new_history = board.ko_history | {after_capture.position_hash(color.opponent)}
    return replace(
        after_capture,
        ko_history=new_history,
        previous_cells=board.cells,
        consecutive_passes=0,
        move_number=board.move_number + 1,
    )


def _flood_region(board: Board, start: Position, seen: set[Position]) -> tuple[
    frozenset[Position], frozenset[int]
]:
    """Flood-fill an empty region starting at ``start``.

    Returns the set of empty positions in the region and the set of stone
    colors (as ints) bordering it.
    """
    region: set[Position] = set()
    borders: set[int] = set()
    stack: list[Position] = [start]
    while stack:
        p = stack.pop()
        if p in region:
            continue
        if board.cells[board.index(*p)] != Color.EMPTY.value:
            borders.add(board.cells[board.index(*p)])
            continue
        region.add(p)
        seen.add(p)
        for n in board.neighbors(*p):
            if n not in region:
                stack.append(n)
    return frozenset(region), frozenset(borders)


def score_area(board: Board, komi: float = 2.5) -> ScoreReport:
    """Score the board using Chinese / Tromp-Taylor area scoring.

    Each player's score is (their stones) + (empties strictly surrounded
    by their color only). White additionally receives ``komi`` points.
    """
    black = 0.0
    white = 0.0
    seen_empty: set[Position] = set()
    for r, c in board.positions():
        v = board.cells[board.index(r, c)]
        if v == Color.BLACK.value:
            black += 1
        elif v == Color.WHITE.value:
            white += 1
        else:
            if (r, c) in seen_empty:
                continue
            region, borders = _flood_region(board, (r, c), seen_empty)
            stone_borders = borders - {Color.EMPTY.value}
            if stone_borders == {Color.BLACK.value}:
                black += len(region)
            elif stone_borders == {Color.WHITE.value}:
                white += len(region)
    white += komi
    if black > white:
        winner = Color.BLACK
    elif white > black:
        winner = Color.WHITE
    else:
        winner = Color.EMPTY
    return {"black": black, "white": white, "winner": winner}


def score_stone_count(board: Board, komi: float = 2.5) -> ScoreReport:
    """Legacy scoring: stones on the board only, plus komi for white.

    This matches ``legacy/stage1/host.py``'s ``judge_winner`` exactly and
    exists for the regression test. Use :func:`score_area` everywhere
    else.
    """
    black = float(sum(1 for v in board.cells if v == Color.BLACK.value))
    white = float(sum(1 for v in board.cells if v == Color.WHITE.value)) + komi
    if black > white:
        winner = Color.BLACK
    elif white > black:
        winner = Color.WHITE
    else:
        winner = Color.EMPTY
    return {"black": black, "white": white, "winner": winner}


__all__ = [
    "ScoreReport",
    "apply_move",
    "is_legal",
    "score_area",
    "score_stone_count",
]
