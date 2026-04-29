"""Regression test: AlphaBetaAgent(legacy=True) must produce the same
move sequence as the original ``legacy/stage1/my_player3.py`` driven
through ``legacy/stage1/host.py``.

Strategy:

1. The first time this test runs, drive the legacy code in-process
   (import its modules from ``legacy/stage1/``) to play 5 games of
   RandomPlayer vs AdvancedGoAgent, alternating colors. Capture the
   move list and the legacy stone-count winner; persist to
   ``tests/data/regression_alphabeta.json``.

2. On subsequent runs, replay each captured game using
   ``AlphaBetaAgent(legacy=True)`` against a ``ScriptedAgent`` that
   plays the captured random opponent moves. Assert move-by-move
   equality and that the stone-count winner matches.

If this test ever fails after a code change to ``alphabeta_agent.py``,
the change must be either:
* an intentional behavior shift, in which case regenerate the golden
  file with a clear commit message, or
* an accidental regression, which must be fixed in the agent.
"""

from __future__ import annotations

import json
import random
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

import pytest

from go_arena.agents.alphabeta_agent import AlphaBetaAgent
from go_arena.agents.base import BaseAgent
from go_arena.engine.board import Board
from go_arena.engine.rules import score_stone_count
from go_arena.engine.types import PASS, Color, Move, Pass, Place
from go_arena.tournament.match import play_match

REPO_ROOT = Path(__file__).resolve().parent.parent
LEGACY_DIR = REPO_ROOT / "legacy" / "stage1"
GOLDEN_PATH = REPO_ROOT / "tests" / "data" / "regression_alphabeta.json"


@dataclass
class GoldenGame:
    seed: int
    legacy_color: int  # color the AdvancedGoAgent played (1 = BLACK, 2 = WHITE)
    moves: list[tuple[int, str]] = field(default_factory=list)  # (color, "PASS" | "r,c")
    legacy_winner: int = 0  # 1 BLACK, 2 WHITE, 0 tie


def _move_to_str(move: Move) -> str:
    if isinstance(move, Pass):
        return "PASS"
    return f"{move.row},{move.col}"


def _str_to_move(text: str) -> Move:
    if text == "PASS":
        return PASS
    r, c = text.split(",")
    return Place(int(r), int(c))


class ScriptedAgent(BaseAgent):
    """Replays a fixed list of moves. Used to feed captured opponent
    moves back into the new engine for regression checking."""

    name = "scripted"

    def __init__(self, moves: list[Move]) -> None:
        self._moves = list(moves)
        self._idx = 0

    def reset(self) -> None:
        self._idx = 0

    def select_move(self, board: Board, color: Color, time_limit: float) -> Move:
        if self._idx >= len(self._moves):
            return PASS
        move = self._moves[self._idx]
        self._idx += 1
        return move


def _generate_golden() -> list[GoldenGame]:
    """Drive legacy code to produce the golden move sequences."""
    sys.path.insert(0, str(LEGACY_DIR))
    try:
        from host import GO  # type: ignore[import-not-found]
        from my_player3 import AdvancedGoAgent  # type: ignore[import-not-found]
        from random_player import RandomPlayer  # type: ignore[import-not-found]
    finally:
        sys.path.remove(str(LEGACY_DIR))

    games: list[GoldenGame] = []
    seeds = [11, 22, 33, 44, 55]
    for game_idx, seed in enumerate(seeds):
        legacy_color = 1 if game_idx % 2 == 0 else 2  # alternate
        random.seed(seed)
        go = GO(5)
        go.init_board(5)
        random_p = RandomPlayer()
        legacy_p = AdvancedGoAgent()

        captured = GoldenGame(seed=seed, legacy_color=legacy_color)
        n_moves = 0
        consecutive_passes = 0
        x_to_play = True  # X (1) plays first
        while n_moves < 80:
            piece_type = 1 if x_to_play else 2
            agent = legacy_p if piece_type == legacy_color else random_p
            if agent is legacy_p:
                action = agent.get_move(go, piece_type)
            else:
                action = agent.get_input(go, piece_type)

            if action == "PASS":
                go.previous_board = [row[:] for row in go.board]
                captured.moves.append((piece_type, "PASS"))
                consecutive_passes += 1
                if consecutive_passes >= 2:
                    break
            else:
                ok = go.place_chess(action[0], action[1], piece_type)
                if not ok:
                    # Forfeit: opponent wins. Mark and break.
                    captured.legacy_winner = 3 - piece_type
                    break
                go.died_pieces = go.remove_died_pieces(3 - piece_type)
                captured.moves.append((piece_type, f"{action[0]},{action[1]}"))
                consecutive_passes = 0

            n_moves += 1
            x_to_play = not x_to_play

        if captured.legacy_winner == 0:
            captured.legacy_winner = go.judge_winner()
        games.append(captured)
    return games


def _load_golden() -> list[GoldenGame]:
    if not GOLDEN_PATH.exists():
        return []
    raw = json.loads(GOLDEN_PATH.read_text())
    return [GoldenGame(**g) for g in raw]


def _save_golden(games: list[GoldenGame]) -> None:
    GOLDEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    GOLDEN_PATH.write_text(json.dumps([asdict(g) for g in games], indent=2))


@pytest.fixture(scope="module")
def golden_games() -> list[GoldenGame]:
    games = _load_golden()
    if not games:
        games = _generate_golden()
        _save_golden(games)
    return games


def test_golden_games_exist_and_have_moves(golden_games: list[GoldenGame]) -> None:
    assert len(golden_games) == 5
    for g in golden_games:
        assert len(g.moves) > 0


def test_alphabeta_legacy_replays_each_golden_game(golden_games: list[GoldenGame]) -> None:
    """Replay every captured game; the legacy alphabeta agent must
    produce identical moves to the original."""
    for game_idx, golden in enumerate(golden_games):
        legacy_color = Color(golden.legacy_color)

        # Split the captured move sequence by side.
        legacy_moves: list[Move] = []
        random_moves: list[Move] = []
        for color_int, text in golden.moves:
            move = _str_to_move(text)
            if color_int == golden.legacy_color:
                legacy_moves.append(move)
            else:
                random_moves.append(move)

        ab = AlphaBetaAgent(legacy=True, time_limit=60.0)
        scripted = ScriptedAgent(random_moves)

        if legacy_color is Color.BLACK:
            black, white = ab, scripted
        else:
            black, white = scripted, ab

        # Use a generous time budget to avoid time-control non-determinism,
        # and simple-ko mode to mirror legacy host.py legality semantics.
        result = play_match(
            black,
            white,
            board_size=5,
            time_limit=60.0,
            max_moves=80,
            score_fn=score_stone_count,
            simple_ko_mode=True,
        )

        # The legacy agent should never forfeit when replaying golden data.
        assert result.forfeit is None, (
            f"Game {game_idx}: forfeit {result.forfeit} — alphabeta produced an "
            f"illegal move while replaying golden moves."
        )

        # Compare the alphabeta-played moves to the golden record.
        replayed_legacy_moves = [
            move for color, move in result.moves if color is legacy_color
        ]
        assert len(replayed_legacy_moves) == len(legacy_moves), (
            f"Game {game_idx}: alphabeta played {len(replayed_legacy_moves)} moves, "
            f"golden has {len(legacy_moves)}."
        )
        for i, (replayed, golden_move) in enumerate(
            zip(replayed_legacy_moves, legacy_moves, strict=True)
        ):
            assert replayed == golden_move, (
                f"Game {game_idx} alphabeta move {i} differs: "
                f"replayed={replayed} golden={golden_move}"
            )

        # Stone-count winner must also match.
        assert result.score["winner"] == Color(golden.legacy_winner) or (
            golden.legacy_winner == 0 and result.score["winner"] == Color.EMPTY
        ), (
            f"Game {game_idx}: winner mismatch — replay {result.score['winner']} "
            f"vs golden {golden.legacy_winner}"
        )
