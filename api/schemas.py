"""Pydantic schemas for the HTTP API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ColorName = Literal["black", "white", "empty"]
GameStatus = Literal["in_progress", "finished", "resigned"]


class AgentInfo(BaseModel):
    """Description of a registered agent."""

    name: str
    label: str
    description: str
    strength: int  # rough ordering, 1 = weakest


class NewGameRequest(BaseModel):
    """Body for ``POST /games``."""

    human_color: ColorName = Field(..., description="The color the human plays.")
    agent: str = Field(..., description="Registered agent name for the opponent.")
    time_limit: float = Field(2.0, ge=0.1, le=30.0, description="Per-move budget (s).")
    board_size: int = Field(5, ge=5, le=5, description="Board edge length (5x5 only).")


class MoveRequest(BaseModel):
    """Body for ``POST /games/{id}/move``."""

    move: str = Field(..., description='"PASS" or "row,col" (0-indexed).')


class MoveRecord(BaseModel):
    """One half-move played in the game."""

    color: ColorName
    move: str  # "PASS" or "r,c"
    by: Literal["human", "agent"]
    elapsed_ms: int


class ScoreInfo(BaseModel):
    black: float
    white: float
    winner: ColorName  # "empty" = tie


class GameState(BaseModel):
    """Full snapshot of a game returned by ``GET /games/{id}``."""

    game_id: str
    status: GameStatus
    human_color: ColorName
    agent_color: ColorName
    agent_name: str
    time_limit: float
    board_size: int
    cells: list[list[int]]  # row-major; 0 empty, 1 black, 2 white
    move_number: int
    consecutive_passes: int
    color_to_play: ColorName
    legal_moves: list[str]  # serialized for the side to play
    last_move: str | None
    moves: list[MoveRecord]
    captures: dict[ColorName, int]
    score: ScoreInfo | None  # None until finished
    agent_thinking: bool


__all__ = [
    "AgentInfo",
    "ColorName",
    "GameState",
    "GameStatus",
    "MoveRecord",
    "MoveRequest",
    "NewGameRequest",
    "ScoreInfo",
]
