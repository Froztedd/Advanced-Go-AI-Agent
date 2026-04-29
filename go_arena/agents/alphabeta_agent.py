"""Negamax + alpha-beta + iterative deepening agent.

Ported from ``legacy/stage1/my_player3.py``. Two modes via the ``legacy``
constructor flag:

* ``legacy=True``: byte-for-byte behavior parity with the CSCI 561
  submission. ``max_depth=3``, top-8 root move pruning, top-5 inside
  negamax, the inconsistent leaf evaluator that ignores the weight
  tables, soft time control with 0.1 s safety margin.

* ``legacy=False`` (default, "improved"): ``max_depth=4``, top-15 root /
  top-10 negamax, leaf evaluator uses the same weighted heuristic as
  move ordering, harder 0.2 s safety margin.
"""

from __future__ import annotations

import time
from typing import TypedDict

from go_arena.agents.base import BaseAgent
from go_arena.engine.board import Board
from go_arena.engine.rules import _captured_groups, apply_move, is_legal
from go_arena.engine.types import PASS, Color, Move, Pass, Place, Position


class _Weights(TypedDict):
    capture: float
    liberty: float
    territory: float
    center: float
    connection: float
    shape: float


_OPENING_WEIGHTS: _Weights = {
    "capture": 9.0,
    "liberty": 7.0,
    "territory": 5.0,
    "center": 6.0,
    "connection": 5.0,
    "shape": 4.0,
}
_MIDGAME_WEIGHTS: _Weights = {
    "capture": 8.0,
    "liberty": 6.0,
    "territory": 6.0,
    "center": 4.0,
    "connection": 6.0,
    "shape": 5.0,
}
_ENDGAME_WEIGHTS: _Weights = {
    "capture": 7.0,
    "liberty": 5.0,
    "territory": 7.0,
    "center": 3.0,
    "connection": 4.0,
    "shape": 3.0,
}

# Patterns matched in legacy/stage1/my_player3.py for "good shape" bonus.
_GOOD_PATTERNS: tuple[tuple[tuple[int, int], ...], ...] = (
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (1, 1)),
    ((0, 0), (0, 1), (1, 1)),
)


def _stone_count(board: Board) -> int:
    return sum(1 for v in board.cells if v != 0)


def _select_weights(stone_count: int) -> _Weights:
    if stone_count < 8:
        return _OPENING_WEIGHTS
    if stone_count < 16:
        return _MIDGAME_WEIGHTS
    return _ENDGAME_WEIGHTS


def _evaluate_position(size: int, row: int, col: int) -> float:
    """Center-distance bonus matching legacy ``evaluate_position``."""
    center = size // 2
    dist = abs(row - center) + abs(col - center)
    if dist == 0:
        return 3.0
    if dist == 1:
        return 2.0
    if dist == 2:
        return 1.0
    return 0.0


def _evaluate_territory(board: Board, start: Position, color: Color) -> float:
    """Direct port of legacy ``evaluate_territory`` BFS."""
    score = 0.0
    visited: set[Position] = set()
    queue: list[Position] = [start]
    while queue:
        x, y = queue.pop(0)
        if (x, y) in visited:
            continue
        visited.add((x, y))
        for nx, ny in board.neighbors(x, y):
            if (nx, ny) in visited:
                continue
            v = board.cells[board.index(nx, ny)]
            if v == 0:
                score += 0.5
                queue.append((nx, ny))
            elif v == color.value:
                score += 1.0
                queue.append((nx, ny))
            else:
                score -= 0.5
    return score


def _forms_good_shape(board: Board, row: int, col: int, color: Color) -> bool:
    for pattern in _GOOD_PATTERNS:
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                ok = True
                for px, py in pattern:
                    x, y = row + px + di, col + py + dj
                    if not (
                        0 <= x < board.size
                        and 0 <= y < board.size
                        and board.cells[board.index(x, y)] == color.value
                    ):
                        ok = False
                        break
                if ok:
                    return True
    return False


def _evaluate_move(
    board: Board, place: Place, color: Color, weights: _Weights, *, legacy: bool
) -> float:
    """One-ply heuristic for ``color`` playing ``place``.

    The ``legacy`` flag mirrors a quirk in
    ``legacy/stage1/my_player3.py``: the original computed the
    "connection" feature as ``state.detect_neighbor_ally(i, j)`` on the
    *pre-placement* state. Since ``state.board[i][j]`` was 0 (empty)
    at that point, ``detect_neighbor_ally`` matched empty neighbors,
    not same-color ones. We mirror that here for behavioural parity;
    the improved variant counts actual same-color allies.
    """
    placed = board.with_stone(place.row, place.col, color)
    captured = _captured_groups(placed, color.opponent)
    after = placed.with_removed(captured)

    libs = len(after.liberties_of((place.row, place.col)))
    territory = _evaluate_territory(after, (place.row, place.col), color)
    position = _evaluate_position(board.size, place.row, place.col)
    if legacy:
        allies = sum(
            1
            for n in board.neighbors(place.row, place.col)
            if board.cells[board.index(*n)] == Color.EMPTY.value
        )
    else:
        allies = sum(
            1
            for n in board.neighbors(place.row, place.col)
            if board.cells[board.index(*n)] == color.value
        )
    shape_bonus = weights["shape"] if _forms_good_shape(after, place.row, place.col, color) else 0.0

    return (
        len(captured) * weights["capture"]
        + libs * weights["liberty"]
        + territory * weights["territory"]
        + position * weights["center"]
        + allies * weights["connection"]
        + shape_bonus
    )


def _is_urgent_defensive_move(board: Board, place: Place, color: Color) -> bool:
    for nr, nc in board.neighbors(place.row, place.col):
        if (
            board.cells[board.index(nr, nc)] == color.value
            and len(board.liberties_of((nr, nc))) <= 2
        ):
            return True
    return False


def _move_priority(
    board: Board,
    place: Place,
    color: Color,
) -> int:
    """Replicates legacy ``get_move_priority``."""
    placed = board.with_stone(place.row, place.col, color)
    captured = _captured_groups(placed, color.opponent)
    priority = 0
    if captured:
        priority += 3
    if _is_urgent_defensive_move(board, place, color):
        priority += 2
    after = placed.with_removed(captured)
    if _forms_good_shape(after, place.row, place.col, color):
        priority += 1
    return priority


def _move_heuristic(size: int, move: Move) -> int:
    """Center-distance secondary key from legacy ``move_heuristic``."""
    if isinstance(move, Pass):
        return -1
    center = size // 2
    return -(abs(move.row - center) + abs(move.col - center))


def _legacy_leaf_evaluation(board: Board, color: Color) -> float:
    """The ±10 + liberty leaf eval from legacy ``evaluate_board`` that
    intentionally ignores the weight tables. Preserved for parity."""
    score = 0.0
    seen_groups: set[Position] = set()
    for r, c in board.positions():
        v = board.cells[board.index(r, c)]
        if v == color.value:
            score += 10.0
            score += len(board.liberties_of((r, c)))
        elif v == color.opponent.value:
            score -= 10.0
            score -= len(board.liberties_of((r, c)))
        else:
            continue
        _ = seen_groups
    return score


def _improved_leaf_evaluation(board: Board, color: Color, weights: _Weights) -> float:
    """Improved leaf eval that re-uses the weighted move heuristic, summed
    over all stones of each color."""
    score = 0.0
    for r, c in board.positions():
        v = board.cells[board.index(r, c)]
        if v == color.value:
            score += _evaluate_move(board, Place(r, c), color, weights, legacy=False)
        elif v == color.opponent.value:
            score -= _evaluate_move(board, Place(r, c), color.opponent, weights, legacy=False)
    return score


def _opening_move(board: Board, color: Color) -> Move | None:
    """Replicates legacy ``handle_opening`` for the first few stones."""
    stones = _stone_count(board)
    if stones == 0:
        return Place(2, 2)
    if board.size == 5 and board.cells[board.index(2, 2)] == color.opponent.value:
        for cr, cc in [(0, 0), (0, 4), (4, 0), (4, 4)]:
            if is_legal(board, Place(cr, cc), color):
                return Place(cr, cc)
    strategic = [
        (2, 2),
        (1, 1),
        (1, 3),
        (3, 1),
        (3, 3),
        (0, 2),
        (2, 0),
        (2, 4),
        (4, 2),
    ]
    for r, c in strategic:
        if 0 <= r < board.size and 0 <= c < board.size and is_legal(
            board, Place(r, c), color
        ):
            return Place(r, c)
    return None


class AlphaBetaAgent(BaseAgent):
    """Negamax + alpha-beta + iterative deepening.

    Construct with ``legacy=True`` to mirror the CSCI 561 submission
    exactly (used by the regression test). Default is the improved
    variant.
    """

    name = "alphabeta"

    def __init__(
        self,
        legacy: bool = False,
        max_depth: int | None = None,
        time_limit: float | None = None,
    ) -> None:
        self.legacy = legacy
        if legacy:
            self.max_depth = 3 if max_depth is None else max_depth
            self.time_limit = 9.5 if time_limit is None else time_limit
            self._safety = 0.1
            # Legacy quirk: get_sorted_moves stores top-8 but the root
            # iteration only walks moves[:min(6, len(moves))].
            self._root_top_n = 8
            self._root_iter_n = 6
            self._negamax_top_n = 5
        else:
            self.max_depth = 4 if max_depth is None else max_depth
            self.time_limit = 9.5 if time_limit is None else time_limit
            self._safety = 0.2
            self._root_top_n = 15
            self._root_iter_n = 15
            self._negamax_top_n = 10

        self._start_time = 0.0
        self._budget = self.time_limit

    def reset(self) -> None:
        self._start_time = 0.0

    def _is_time_up(self) -> bool:
        return time.time() - self._start_time > self._budget - self._safety

    def select_move(self, board: Board, color: Color, time_limit: float) -> Move:
        self._start_time = time.time()
        # The agent's intrinsic budget; honor whichever is tighter.
        self._budget = min(self.time_limit, time_limit)

        stones = _stone_count(board)
        weights = _select_weights(stones)

        if stones <= 4:
            opening = _opening_move(board, color)
            if opening is not None:
                return opening

        sorted_moves = self._sorted_moves(board, color, weights, top_n=self._root_top_n)
        if not sorted_moves:
            return PASS

        best_move: Move = sorted_moves[0][1]
        best_score: float = sorted_moves[0][0]
        alpha = float("-inf")
        beta = float("inf")

        max_depth = min(self.max_depth, 24 - stones)
        for depth in range(1, max_depth + 1):
            if self._is_time_up():
                break
            current_best: Move | None = None
            current_score = float("-inf")
            for _score, move, _prio in sorted_moves[: min(self._root_iter_n, len(sorted_moves))]:
                if self._is_time_up():
                    break
                assert isinstance(move, Place)
                after = apply_move(board, move, color)
                eval_score = -self._negamax(
                    after, depth - 1, color.opponent, -beta, -alpha, weights
                )
                if eval_score > current_score or (
                    eval_score == current_score
                    and _move_heuristic(board.size, move)
                    > _move_heuristic(board.size, current_best or PASS)
                ):
                    current_score = eval_score
                    current_best = move
                    alpha = max(alpha, eval_score)
            if current_best is not None and not self._is_time_up() and (
                current_score > best_score
                or (
                    current_score == best_score
                    and _move_heuristic(board.size, current_best)
                    > _move_heuristic(board.size, best_move)
                )
            ):
                best_score = current_score
                best_move = current_best
        return best_move

    def _sorted_moves(
        self,
        board: Board,
        color: Color,
        weights: _Weights,
        top_n: int,
    ) -> list[tuple[float, Place, int]]:
        scored: list[tuple[float, Place, int]] = []
        for move in board.legal_moves(color):
            if not isinstance(move, Place):
                continue
            score = _evaluate_move(board, move, color, weights, legacy=self.legacy)
            priority = _move_priority(board, move, color)
            scored.append((score, move, priority))
        scored.sort(
            key=lambda item: (-item[0], -item[2], -_move_heuristic(board.size, item[1]))
        )
        return scored[:top_n]

    def _negamax(
        self,
        board: Board,
        depth: int,
        color: Color,
        alpha: float,
        beta: float,
        weights: _Weights,
    ) -> float:
        if depth == 0 or self._is_time_up() or board.is_terminal:
            if self.legacy:
                return _legacy_leaf_evaluation(board, color)
            return _improved_leaf_evaluation(board, color, weights)

        sorted_moves = self._sorted_moves(board, color, weights, top_n=self._negamax_top_n)
        if not sorted_moves:
            return 0.0

        best = float("-inf")
        for _score, move, _prio in sorted_moves:
            if self._is_time_up():
                break
            after = apply_move(board, move, color)
            value = -self._negamax(after, depth - 1, color.opponent, -beta, -alpha, weights)
            if value > best:
                best = value
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return best


__all__ = ["AlphaBetaAgent"]
