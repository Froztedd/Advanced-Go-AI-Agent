"""Plain depth-2 minimax (no alpha-beta pruning)."""

from __future__ import annotations

from go_arena.agents.base import BaseAgent
from go_arena.engine.board import Board
from go_arena.engine.rules import apply_move
from go_arena.engine.types import PASS, Color, Move, Place, Position


def _leaf_score(board: Board, color: Color) -> float:
    """Material balance with a liberty bonus.

    ``+10`` per own stone, ``-10`` per opponent stone, plus the total
    number of liberties of own groups minus opponent groups. This is a
    pure board evaluator (unlike greedy's per-move heuristic) and gives
    captures their full weight at depth.
    """
    own_stones = 0
    opp_stones = 0
    own_libs = 0
    opp_libs = 0
    seen: set[Position] = set()
    for r, c in board.positions():
        v = board.cells[board.index(r, c)]
        if v == 0:
            continue
        if v == color.value:
            own_stones += 1
        else:
            opp_stones += 1
        if (r, c) in seen:
            continue
        group = board.group_at((r, c))
        seen.update(group)
        libs = len(board.liberties_of((r, c)))
        if v == color.value:
            own_libs += libs
        else:
            opp_libs += libs
    return 10.0 * (own_stones - opp_stones) + (own_libs - opp_libs)


class MinimaxAgent(BaseAgent):
    """Depth-2 minimax. Useful as the strict midpoint between greedy
    and alpha-beta: same eval, no pruning, no iterative deepening.
    """

    name = "minimax"

    def __init__(self, depth: int = 2) -> None:
        self.depth = depth

    def select_move(self, board: Board, color: Color, time_limit: float) -> Move:
        best_move: Move = PASS
        best_score = float("-inf")
        for move in board.legal_moves(color):
            if not isinstance(move, Place):
                continue
            after = apply_move(board, move, color)
            score = -self._negamax(after, self.depth - 1, color.opponent)
            if score > best_score:
                best_score = score
                best_move = move
        return best_move

    def _negamax(self, board: Board, depth: int, color: Color) -> float:
        if depth == 0 or board.is_terminal:
            return _leaf_score(board, color)
        best = float("-inf")
        any_move = False
        for move in board.legal_moves(color):
            if not isinstance(move, Place):
                continue
            any_move = True
            after = apply_move(board, move, color)
            score = -self._negamax(after, depth - 1, color.opponent)
            if score > best:
                best = score
        if not any_move:
            return _leaf_score(board, color)
        return best


__all__ = ["MinimaxAgent"]
