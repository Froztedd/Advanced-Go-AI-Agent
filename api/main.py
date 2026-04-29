"""FastAPI app exposing the go-arena engine over HTTP."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from go_arena.agents import REGISTRY
from go_arena.engine.types import Color

from api.schemas import AgentInfo, GameState, MoveRequest, NewGameRequest
from api.store import (
    GameStore,
    apply_agent_move,
    apply_human_move,
    name_to_color,
    resign,
)

app = FastAPI(
    title="go-arena",
    version="0.2.0",
    description="A 5x5 Go arena with multiple AI agents.",
)

# Permissive CORS for local dev. Lock down before any public deploy.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

_store = GameStore()


_AGENT_LABELS: dict[str, tuple[str, str, int]] = {
    "random": (
        "Random",
        "Picks any legal move uniformly at random. Easy.",
        1,
    ),
    "greedy": (
        "Greedy",
        "One-ply heuristic: weights captures, liberties, and center control. No search.",
        2,
    ),
    "minimax": (
        "Minimax",
        "Depth-2 plain minimax. Same eval as greedy, applied at depth.",
        3,
    ),
    "alphabeta-legacy": (
        "Alpha-Beta (legacy)",
        "The original CSCI 561 submission, byte-for-byte. Slightly weaker than the improved variant.",
        4,
    ),
    "alphabeta": (
        "Alpha-Beta",
        "Negamax + alpha-beta + iterative deepening, depth 4. Phase-aware heuristic, opening book.",
        5,
    ),
}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/agents", response_model=list[AgentInfo])
def list_agents() -> list[AgentInfo]:
    out: list[AgentInfo] = []
    for name in REGISTRY:
        label, description, strength = _AGENT_LABELS.get(
            name, (name.title(), "", 0)
        )
        out.append(
            AgentInfo(
                name=name, label=label, description=description, strength=strength
            )
        )
    out.sort(key=lambda a: (a.strength, a.label))
    return out


@app.post("/games", response_model=GameState)
def create_game(req: NewGameRequest) -> GameState:
    if req.agent not in REGISTRY:
        raise HTTPException(status_code=400, detail=f"Unknown agent {req.agent!r}")
    try:
        session = _store.create(
            human_color_name=req.human_color,
            agent_name=req.agent,
            time_limit=req.time_limit,
            board_size=req.board_size,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # If the agent plays Black, let it move first so the client opens with a
    # board that already shows the agent's opening stone.
    if session.agent_color is Color.BLACK:
        apply_agent_move(session)

    return session.snapshot()


@app.get("/games/{game_id}", response_model=GameState)
def get_game(game_id: str) -> GameState:
    session = _store.get(game_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return session.snapshot()


@app.post("/games/{game_id}/move", response_model=GameState)
def make_move(game_id: str, req: MoveRequest) -> GameState:
    session = _store.get(game_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Game not found")
    try:
        apply_human_move(session, req.move)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # If the game isn't over and it's now the agent's turn, let it respond
    # synchronously. Time budgets are small enough (default 2 s) that we
    # do not need a background queue for the demo.
    if (
        session.status == "in_progress"
        and session.color_to_play is session.agent_color
    ):
        try:
            apply_agent_move(session)
        except ValueError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    return session.snapshot()


@app.post("/games/{game_id}/resign", response_model=GameState)
def resign_game(game_id: str) -> GameState:
    session = _store.get(game_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Game not found")
    try:
        resign(session, session.human_color)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return session.snapshot()


__all__ = ["app"]
