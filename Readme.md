# go-arena

A 5x5 Go arena with multiple AI agents (random, greedy, minimax, alpha-beta, AlphaZero).

Phase 2 ships a playable web demo: pick a color, pick an opponent, watch stones drop on a wood-grain board with live AI moves. Full README rewrite lands in Phase 5.

## Status

- [x] **Phase 1** — Engine, 5 agents, CLI, 65 tests, 96% coverage, regression test against legacy.
- [x] **Phase 2** — FastAPI backend + React/TypeScript/Tailwind/GSAP frontend. Playable end to end.
- [ ] Phase 3 — AlphaZero-lite (PyTorch + MCTS, self-play training).
- [ ] Phase 4 — Round-robin tournament + Elo leaderboard.
- [ ] Phase 5 — Polish, blog post, deploy.

## Play it locally

You need Python 3.11+ and Node 18+. Both backend deps and the FastAPI server are already on most Python setups; install if missing:

```
pip install fastapi uvicorn pydantic
cd web && npm install && cd ..
```

Then run both servers (one terminal):

```
./scripts/dev.sh
```

Or in two terminals:

```
# terminal 1 — API on :8000
uvicorn api.main:app --reload --port 8000

# terminal 2 — frontend on :5173
cd web && npm run dev
```

Open **http://localhost:5173** and play.

## Backend CLI (no browser)

```
pip install -e .[dev]
python -m go_arena agents
python -m go_arena play --black=alphabeta --white=greedy --time=2
pytest
```

## The five agents

| Name | Algorithm | Notes |
| --- | --- | --- |
| `random` | Uniform random over legal placements | Passes when no placement is legal. |
| `greedy` | One-ply heuristic: capture, liberty, center, connection | No search. |
| `minimax` | Depth-2 plain minimax (no alpha-beta) | Material + liberty leaf eval. |
| `alphabeta` | Negamax + alpha-beta + iterative deepening | Default. Improved variant of the original CSCI 561 agent: depth 4, top-15/10 move pruning, weighted leaf eval. |
| `alphabeta-legacy` | Same algorithm | Byte-for-byte parity with the original submission: depth 3, top-8/5 pruning, original quirks preserved. Used by the regression test. |

## Repo layout

```
go_arena/        # Python: engine, agents, tournament runner, CLI
api/             # FastAPI app: /agents, /games, /games/{id}/move, /resign
web/             # Vite + React + TypeScript + Tailwind + GSAP frontend
scripts/dev.sh   # Run backend + frontend together
tests/           # 65 tests covering engine, agents, regression, perf
legacy/stage1/   # Untouched CSCI 561 submission, kept for diffing
FINDINGS.md      # Phase 0 analysis of the legacy code and refactor plan
```

## API surface

| Method | Path                     | Purpose                                          |
| ------ | ------------------------ | ------------------------------------------------ |
| GET    | `/health`                | Liveness probe.                                  |
| GET    | `/agents`                | Registered agents with labels and descriptions.  |
| POST   | `/games`                 | Start a new game; body: `{human_color, agent, time_limit, board_size}`. |
| GET    | `/games/{id}`            | Snapshot: board, legal moves, captures, score.   |
| POST   | `/games/{id}/move`       | Play a human move (`"PASS"` or `"r,c"`); returns the post-AI-response state. |
| POST   | `/games/{id}/resign`     | Concede the game.                                |

OpenAPI docs at `http://localhost:8000/docs` once the backend is running.

## Why two scoring functions

`go_arena.engine.rules.score_area` is Chinese / Tromp-Taylor area scoring (stones + surrounded empties + komi for white). It is the default everywhere in new code. `score_stone_count` matches the legacy host's stone-only scoring exactly and is used by the regression test for parity.

## Why `simple_ko_mode`

The new engine enforces full positional superko by default (the proper rule). The legacy CSCI 561 host enforced only "simple ko" (a one-step-back board comparison after a capture). The regression test sets `Board(simple_ko_mode=True)` so legacy moves replay legally; production play uses superko.
