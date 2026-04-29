"""In-memory game store + game state tracking.

Each game tracks a :class:`Board`, the agents, and the move history. The
store is a process-local dict; a server restart wipes all games. Good
enough for the local demo; persistence is a later concern.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from threading import Lock

from go_arena.agents import make_agent
from go_arena.agents.base import BaseAgent
from go_arena.engine.board import Board, IllegalMove
from go_arena.engine.rules import apply_move, score_area
from go_arena.engine.types import PASS, Color, Move, Pass, Place, parse_move

from api.schemas import (
    ColorName,
    GameState,
    MoveRecord,
    ScoreInfo,
)


def color_to_name(color: Color) -> ColorName:
    return {Color.BLACK: "black", Color.WHITE: "white", Color.EMPTY: "empty"}[color]


def name_to_color(name: ColorName) -> Color:
    return {"black": Color.BLACK, "white": Color.WHITE, "empty": Color.EMPTY}[name]


def move_to_str(move: Move) -> str:
    if isinstance(move, Pass):
        return "PASS"
    return f"{move.row},{move.col}"


@dataclass
class GameSession:
    """A single in-progress or finished game."""

    game_id: str
    human_color: Color
    agent_color: Color
    agent_name: str
    agent: BaseAgent
    time_limit: float
    board: Board
    status: str = "in_progress"  # "in_progress" | "finished" | "resigned"
    moves: list[MoveRecord] = field(default_factory=list)
    captures: dict[Color, int] = field(default_factory=lambda: {Color.BLACK: 0, Color.WHITE: 0})
    last_move: Move | None = None
    color_to_play: Color = Color.BLACK
    agent_thinking: bool = False
    resigned_color: Color | None = None

    def snapshot(self) -> GameState:
        """Return a JSON-serializable snapshot for the API."""
        cells = [
            [self.board.cells[self.board.index(r, c)] for c in range(self.board.size)]
            for r in range(self.board.size)
        ]
        legal = [move_to_str(m) for m in self.board.legal_moves(self.color_to_play)]
        score: ScoreInfo | None = None
        if self.status in ("finished", "resigned"):
            if self.status == "resigned" and self.resigned_color is not None:
                # Resignation: opponent wins; surface the running area score for context.
                rep = score_area(self.board)
                winner = self.resigned_color.opponent
                score = ScoreInfo(
                    black=rep["black"],
                    white=rep["white"],
                    winner=color_to_name(winner),
                )
            else:
                rep = score_area(self.board)
                score = ScoreInfo(
                    black=rep["black"],
                    white=rep["white"],
                    winner=color_to_name(rep["winner"]),
                )
        return GameState(
            game_id=self.game_id,
            status=self.status,  # type: ignore[arg-type]
            human_color=color_to_name(self.human_color),
            agent_color=color_to_name(self.agent_color),
            agent_name=self.agent_name,
            time_limit=self.time_limit,
            board_size=self.board.size,
            cells=cells,
            move_number=self.board.move_number,
            consecutive_passes=self.board.consecutive_passes,
            color_to_play=color_to_name(self.color_to_play),
            legal_moves=legal,
            last_move=move_to_str(self.last_move) if self.last_move is not None else None,
            moves=list(self.moves),
            captures={
                "black": self.captures[Color.BLACK],
                "white": self.captures[Color.WHITE],
                "empty": 0,
            },  # type: ignore[arg-type]
            score=score,
            agent_thinking=self.agent_thinking,
        )


class GameStore:
    """Thread-safe in-memory game store."""

    def __init__(self) -> None:
        self._games: dict[str, GameSession] = {}
        self._lock = Lock()

    def create(
        self,
        human_color_name: ColorName,
        agent_name: str,
        time_limit: float,
        board_size: int,
    ) -> GameSession:
        if human_color_name not in ("black", "white"):
            raise ValueError("human_color must be 'black' or 'white'")
        agent = make_agent(agent_name)
        human_color = name_to_color(human_color_name)
        agent_color = human_color.opponent
        session = GameSession(
            game_id=uuid.uuid4().hex[:12],
            human_color=human_color,
            agent_color=agent_color,
            agent_name=agent_name,
            agent=agent,
            time_limit=time_limit,
            board=Board.empty(board_size),
            color_to_play=Color.BLACK,
        )
        with self._lock:
            self._games[session.game_id] = session
        return session

    def get(self, game_id: str) -> GameSession | None:
        with self._lock:
            return self._games.get(game_id)

    def all(self) -> list[GameSession]:
        with self._lock:
            return list(self._games.values())


def apply_human_move(session: GameSession, raw_move: str) -> None:
    """Apply a human-side move, updating capture counts and turn."""
    if session.status != "in_progress":
        raise ValueError(f"Cannot move in a {session.status} game")
    if session.color_to_play is not session.human_color:
        raise ValueError("It is not the human's turn")
    move = parse_move(raw_move)
    _apply_and_record(session, move, by="human")


def apply_agent_move(session: GameSession) -> MoveRecord:
    """Ask the agent for a move and apply it."""
    if session.status != "in_progress":
        raise ValueError(f"Cannot move in a {session.status} game")
    if session.color_to_play is not session.agent_color:
        raise ValueError("It is not the agent's turn")
    session.agent_thinking = True
    try:
        move = session.agent.select_move(
            session.board, session.agent_color, session.time_limit
        )
        return _apply_and_record(session, move, by="agent")
    finally:
        session.agent_thinking = False


def _apply_and_record(session: GameSession, move: Move, *, by: str) -> MoveRecord:
    color = session.color_to_play
    start = time.time()
    pre_opp_count = sum(
        1 for v in session.board.cells if v == color.opponent.value
    )
    try:
        new_board = apply_move(session.board, move, color)
    except IllegalMove as exc:
        raise ValueError(f"Illegal move: {exc}") from exc
    elapsed_ms = int((time.time() - start) * 1000)
    post_opp_count = sum(
        1 for v in new_board.cells if v == color.opponent.value
    )
    captured = max(0, pre_opp_count - post_opp_count)
    session.captures[color] += captured
    session.board = new_board
    session.last_move = move
    record = MoveRecord(
        color=color_to_name(color),
        move=move_to_str(move),
        by=by,  # type: ignore[arg-type]
        elapsed_ms=elapsed_ms,
    )
    session.moves.append(record)
    session.color_to_play = color.opponent
    if session.board.is_terminal:
        session.status = "finished"
    return record


def resign(session: GameSession, color: Color) -> None:
    if session.status != "in_progress":
        raise ValueError("Game already over")
    session.status = "resigned"
    session.resigned_color = color


__all__ = [
    "GameSession",
    "GameStore",
    "apply_agent_move",
    "apply_human_move",
    "color_to_name",
    "move_to_str",
    "name_to_color",
    "resign",
]
