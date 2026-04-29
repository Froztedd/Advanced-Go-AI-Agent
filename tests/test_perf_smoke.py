"""Performance smoke test: 50 random vs random games complete fast.

This exists to catch deepcopy regressions in the engine. If someone
accidentally re-introduces deep state copying, this test will start
timing out.
"""

from __future__ import annotations

import time

from go_arena.agents.random_agent import RandomAgent
from go_arena.tournament.match import play_match


def test_50_random_random_games_under_10_seconds() -> None:
    start = time.time()
    for i in range(50):
        b = RandomAgent(seed=i * 2)
        w = RandomAgent(seed=i * 2 + 1)
        play_match(b, w, time_limit=0.5, max_moves=60)
    elapsed = time.time() - start
    assert elapsed < 10.0, f"50 random games took {elapsed:.2f}s, threshold 10s"
