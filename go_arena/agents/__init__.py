"""Agent registry: central lookup for the CLI and FastAPI backend."""

from __future__ import annotations

from collections.abc import Callable

from go_arena.agents.alphabeta_agent import AlphaBetaAgent
from go_arena.agents.base import BaseAgent
from go_arena.agents.greedy_agent import GreedyAgent
from go_arena.agents.minimax_agent import MinimaxAgent
from go_arena.agents.random_agent import RandomAgent

AgentFactory = Callable[[], BaseAgent]

REGISTRY: dict[str, AgentFactory] = {
    "random": RandomAgent,
    "greedy": GreedyAgent,
    "minimax": MinimaxAgent,
    "alphabeta": lambda: AlphaBetaAgent(legacy=False),
    "alphabeta-legacy": lambda: AlphaBetaAgent(legacy=True),
}


def make_agent(name: str) -> BaseAgent:
    """Construct a registered agent by name."""
    if name not in REGISTRY:
        known = ", ".join(sorted(REGISTRY))
        raise KeyError(f"Unknown agent {name!r}. Known: {known}")
    return REGISTRY[name]()


def list_agents() -> list[str]:
    """Return the registered agent names, sorted."""
    return sorted(REGISTRY)


__all__ = [
    "REGISTRY",
    "AlphaBetaAgent",
    "BaseAgent",
    "GreedyAgent",
    "MinimaxAgent",
    "RandomAgent",
    "list_agents",
    "make_agent",
]
