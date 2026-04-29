"""Base agent interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from go_arena.engine.board import Board
from go_arena.engine.types import Color, Move


class BaseAgent(ABC):
    """Abstract base for all Go agents.

    Concrete agents must set ``name`` and implement :meth:`select_move`.
    Agents may carry per-move state (a transposition table, a network)
    but must not assume anything persists across games; the tournament
    runner calls :meth:`reset` between games.
    """

    name: str = "base"

    @abstractmethod
    def select_move(self, board: Board, color: Color, time_limit: float) -> Move:
        """Return the agent's chosen move for ``color`` on ``board``.

        Args:
            board: Current position.
            color: Side the agent is playing this turn.
            time_limit: Soft wall-clock budget in seconds. Agents are
                expected to honour this, with their own safety margin.

        Returns:
            A legal :class:`Move` (placement or pass).
        """

    def reset(self) -> None:
        """Clear any per-game state. Default is a no-op."""
        return None


__all__ = ["BaseAgent"]
