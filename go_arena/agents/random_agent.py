"""Uniform random agent."""

from __future__ import annotations

import random

from go_arena.agents.base import BaseAgent
from go_arena.engine.board import Board
from go_arena.engine.types import PASS, Color, Move, Place


class RandomAgent(BaseAgent):
    """Picks a uniformly random legal placement.

    Mirrors ``legacy/stage1/random_player.py``: when no placement is
    legal it returns :data:`go_arena.engine.types.PASS`.
    """

    name = "random"

    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)

    def select_move(self, board: Board, color: Color, time_limit: float) -> Move:
        legal = [m for m in board.legal_moves(color) if isinstance(m, Place)]
        if not legal:
            return PASS
        return self._rng.choice(legal)


__all__ = ["RandomAgent"]
