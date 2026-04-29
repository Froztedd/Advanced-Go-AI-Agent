"""Smoke tests for every registered agent."""

from __future__ import annotations

import pytest

from go_arena.agents import REGISTRY, make_agent
from go_arena.engine.board import Board
from go_arena.engine.rules import is_legal
from go_arena.engine.types import Color, Pass, Place


@pytest.fixture(params=sorted(REGISTRY))
def agent_name(request: pytest.FixtureRequest) -> str:
    return str(request.param)


def test_each_agent_returns_legal_move_on_empty_board(agent_name: str) -> None:
    agent = make_agent(agent_name)
    b = Board.empty(5)
    move = agent.select_move(b, Color.BLACK, time_limit=1.0)
    assert isinstance(move, (Pass, Place))
    assert is_legal(b, move, Color.BLACK)


def test_each_agent_passes_when_only_pass_is_legal(agent_name: str) -> None:
    """Build a board where no placement is legal at all (board is full),
    forcing every agent to pass."""
    cells = [Color.WHITE.value] * 25
    cells[0] = Color.BLACK.value  # one black stone so the board isn't pure-W
    b = Board(size=5, cells=tuple(cells))
    legal = b.legal_moves(Color.BLACK)
    assert all(isinstance(m, Pass) for m in legal)

    agent = make_agent(agent_name)
    move = agent.select_move(b, Color.BLACK, time_limit=1.0)
    assert isinstance(move, Pass)


def _capture_in_one_position() -> Board:
    """Setup where Black has a single, obvious capture available.

    A White stone at (1,1) has liberties only at (1,0). Black to play.
    """
    cells = [Color.EMPTY.value] * 25
    cells[0 * 5 + 1] = Color.BLACK.value
    cells[1 * 5 + 1] = Color.WHITE.value
    cells[1 * 5 + 2] = Color.BLACK.value
    cells[2 * 5 + 1] = Color.BLACK.value
    return Board(size=5, cells=tuple(cells))


@pytest.mark.parametrize("agent_name", ["greedy", "minimax"])
def test_agent_takes_obvious_capture(agent_name: str) -> None:
    """Greedy and minimax should never miss a free capture in an
    isolated 1-stone-atari position. AlphaBeta is intentionally excluded
    here: its weighted heuristic legitimately balances captures against
    center / connection / territory and may prefer a strong central
    move over a small material gain. The regression test pins its
    actual move sequence."""
    b = _capture_in_one_position()
    agent = make_agent(agent_name)
    move = agent.select_move(b, Color.BLACK, time_limit=2.0)
    assert isinstance(move, Place)
    assert (move.row, move.col) == (1, 0)


def test_random_agent_seed_reproducibility() -> None:
    from go_arena.agents.random_agent import RandomAgent

    a = RandomAgent(seed=42)
    b = RandomAgent(seed=42)
    board = Board.empty(5)
    moves_a = [a.select_move(board, Color.BLACK, 1.0) for _ in range(5)]
    moves_b = [b.select_move(board, Color.BLACK, 1.0) for _ in range(5)]
    assert moves_a == moves_b


def test_alphabeta_legacy_and_improved_distinct() -> None:
    """Both modes can be constructed; they have different defaults."""
    from go_arena.agents.alphabeta_agent import AlphaBetaAgent

    legacy = AlphaBetaAgent(legacy=True)
    improved = AlphaBetaAgent(legacy=False)
    assert legacy.max_depth == 3
    assert improved.max_depth == 4
    assert legacy._safety < improved._safety
