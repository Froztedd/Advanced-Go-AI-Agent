"""One-ply greedy agent."""

from __future__ import annotations

from go_arena.agents.base import BaseAgent
from go_arena.engine.board import Board
from go_arena.engine.rules import _captured_groups
from go_arena.engine.types import PASS, Color, Move, Place


def _center_bonus(size: int, row: int, col: int) -> float:
    """Manhattan-distance bonus to the board center."""
    center = size // 2
    dist = abs(row - center) + abs(col - center)
    return max(0.0, 3.0 - dist)


def evaluate_placement(board: Board, place: Place, color: Color) -> float:
    """Return a one-ply score for ``color`` playing ``place``.

    Components:
        + 10.0 per captured opponent stone (the agent is named greedy
          for a reason: a free capture should always dominate)
        +  1.0 per liberty of the resulting placed group
        +     center bonus (3 / 2 / 1 / 0)
        +  0.5 per same-color neighbor at the placement (connection)
    """
    after = board.with_stone(place.row, place.col, color)
    captured = _captured_groups(after, color.opponent)
    after = after.with_removed(captured)
    libs = len(after.liberties_of((place.row, place.col)))
    connection = sum(
        1
        for n in board.neighbors(place.row, place.col)
        if board.cells[board.index(*n)] == color.value
    )
    return (
        10.0 * len(captured)
        + 1.0 * libs
        + _center_bonus(board.size, place.row, place.col)
        + 0.5 * connection
    )


class GreedyAgent(BaseAgent):
    """Picks the legal placement with the highest one-ply heuristic.

    Tiebreakers in order: highest score, smallest Manhattan distance to
    the center, then lexicographic (row, col). If no placement is legal
    the agent passes.
    """

    name = "greedy"

    def select_move(self, board: Board, color: Color, time_limit: float) -> Move:
        best: tuple[float, int, int, int] | None = None
        best_move: Move = PASS
        center = board.size // 2
        for move in board.legal_moves(color):
            if not isinstance(move, Place):
                continue
            score = evaluate_placement(board, move, color)
            center_dist = abs(move.row - center) + abs(move.col - center)
            key = (-score, center_dist, move.row, move.col)
            if best is None or key < best:
                best = key
                best_move = move
        return best_move


__all__ = ["GreedyAgent", "evaluate_placement"]
