"""Run a match between two agents."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field

from go_arena.agents.base import BaseAgent
from go_arena.engine.board import Board, IllegalMove
from go_arena.engine.rules import ScoreReport, apply_move, score_area
from go_arena.engine.types import Color, Move


@dataclass(slots=True)
class MatchResult:
    """Outcome of a single match.

    Attributes:
        winner: Color of the winner. ``Color.EMPTY`` for a tie.
        score: Score report from the chosen scoring function.
        moves: Full list of (color, move) pairs in play order.
        time_used: Total seconds spent thinking, per color.
        forfeit: If non-None, the color that forfeited and why.
        final_board: The terminal board state.
    """

    winner: Color
    score: ScoreReport
    moves: list[tuple[Color, Move]] = field(default_factory=list)
    time_used: dict[Color, float] = field(
        default_factory=lambda: {Color.BLACK: 0.0, Color.WHITE: 0.0}
    )
    forfeit: tuple[Color, str] | None = None
    final_board: Board | None = None


def play_match(
    black: BaseAgent,
    white: BaseAgent,
    *,
    board_size: int = 5,
    time_limit: float = 2.0,
    max_moves: int = 100,
    komi: float = 2.5,
    score_fn: Callable[[Board, float], ScoreReport] = score_area,
    on_move: Callable[[Board, Color, Move], None] | None = None,
    simple_ko_mode: bool = False,
) -> MatchResult:
    """Play a full match and return the :class:`MatchResult`.

    Args:
        black: Agent playing Black.
        white: Agent playing White.
        board_size: Board edge length, default 5.
        time_limit: Per-move soft time budget in seconds.
        max_moves: Hard upper bound on total moves played, after which
            the game is scored as-is.
        komi: White's bonus added by the scoring function.
        score_fn: Scoring function — defaults to area scoring. Pass
            :func:`go_arena.engine.rules.score_stone_count` for legacy
            parity tests.
        on_move: Optional callback invoked after each move, receiving
            the post-move board, the color that just moved, and the move.
    """
    black.reset()
    white.reset()

    board = Board.empty(board_size, simple_ko_mode=simple_ko_mode)
    result = MatchResult(winner=Color.EMPTY, score={"black": 0.0, "white": 0.0, "winner": Color.EMPTY})

    color_to_play = Color.BLACK
    while not board.is_terminal and board.move_number < max_moves:
        agent = black if color_to_play is Color.BLACK else white
        start = time.time()
        try:
            move = agent.select_move(board, color_to_play, time_limit)
        except Exception as exc:
            elapsed = time.time() - start
            result.time_used[color_to_play] += elapsed
            result.forfeit = (color_to_play, f"raised {type(exc).__name__}: {exc}")
            result.winner = color_to_play.opponent
            result.score = score_fn(board, komi)
            result.score["winner"] = result.winner
            result.final_board = board
            return result
        elapsed = time.time() - start
        result.time_used[color_to_play] += elapsed

        try:
            board = apply_move(board, move, color_to_play)
        except IllegalMove as exc:
            result.forfeit = (color_to_play, f"illegal move {move!r}: {exc}")
            result.winner = color_to_play.opponent
            result.score = score_fn(board, komi)
            result.score["winner"] = result.winner
            result.final_board = board
            return result

        result.moves.append((color_to_play, move))
        if on_move is not None:
            on_move(board, color_to_play, move)
        color_to_play = color_to_play.opponent

    result.score = score_fn(board, komi)
    result.winner = result.score["winner"]
    result.final_board = board
    return result


__all__ = ["MatchResult", "play_match"]
