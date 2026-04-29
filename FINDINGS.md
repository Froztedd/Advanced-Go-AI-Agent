# Phase 0 — Findings & Refactor Plan

This document captures the current state of the repo, how the existing
agent works, the bugs and dead code I found, and the concrete refactor
required before Phase 1 can start.

## 1. Repo inventory

The entire project lives under [Stage 1/](Stage 1/) plus a top-level
[Readme.md](Readme.md). Nothing is packaged; there is no `pyproject.toml`,
no `requirements.txt`, no test suite, and no module structure.

| File | Lines | Size | Purpose |
| --- | --- | --- | --- |
| [Readme.md](Readme.md) | 106 | 3.7 KB | High-level description of the agent (negamax + alpha-beta + iterative deepening). Slightly out of date — mentions weights `edge` and `corner` that the actual agent does not use. |
| [Stage 1/host.py](Stage 1/host.py) | 464 | 15 KB | The CSCI 561 game host. Defines the `GO` class (board state, capture/liberty/ko, scoring) and a `judge(...)` driver that reads `input.txt`, applies the move from `output.txt`, validates it, exits with the appropriate status code, and writes the next `input.txt`. |
| [Stage 1/my_player3.py](Stage 1/my_player3.py) | 351 | 12 KB | The submitted agent — `AdvancedGoAgent` (negamax + alpha-beta + iterative deepening, phase-specific weights, opening book). This is the agent the rest of the project will use as the "alphabeta" baseline. |
| [Stage 1/75.py](Stage 1/75.py) | 214 | 7.2 KB | An earlier / alternative version of `AdvancedGoAgent`. Same idea, simpler weights, monkey-patches `detect_neighbor_empty`/`detect_neighbor_ally`/`detect_liberties` onto `GO`. Filename suggests it scored 75% on the autograder. **Dead code** — superseded by `my_player3.py`. |
| [Stage 1/random_player.py](Stage 1/random_player.py) | 37 | 1.0 KB | The TA-provided baseline. Picks a uniform random legal move, returns `"PASS"` if none. Has a `.type = 'random'` attribute used by `host.GO.play()`. |
| [Stage 1/read.py](Stage 1/read.py) | 30 | 0.7 KB | `readInput(n)` parses the 11-line `input.txt` (1 line piece type + 5 lines previous board + 5 lines current board). `readOutput()` parses `output.txt`. |
| [Stage 1/write.py](Stage 1/write.py) | 26 | 0.7 KB | `writeOutput(action)` writes either `"PASS"` or `"row,col"`. `writeNextInput(...)` re-emits an `input.txt` for the next move. |
| [Stage 1/build.sh](Stage 1/build.sh) | 165 | 3.7 KB | Bash harness that auto-detects the player language, then runs `random_player.py` vs `my_player3.py` for a configurable number of rounds, alternating colors. The whole thing is glued together via repeatedly invoking `host.py -m N` between every move. |
| [Stage 1/init/input.txt](Stage 1/init/input.txt) | 11 | 60 B | Empty initial board plus piece type 2 — the game start state. |
| [Stage 1/init/output.txt](Stage 1/init/output.txt) | 0 | 0 B | Empty placeholder. |
| [Stage 1/.DS_Store](Stage 1/.DS_Store) | — | 6 KB | macOS Finder cruft. Will be deleted and `.gitignore`d. |

## 2. Existing agent — `AdvancedGoAgent` ([Stage 1/my_player3.py](Stage 1/my_player3.py))

### 2.1 Algorithm

- **Search:** negamax with alpha-beta pruning ([Stage 1/my_player3.py:295](Stage 1/my_player3.py#L295)) — depth-first, returning the best score from the side-to-move's perspective and negating across recursive calls.
- **Iterative deepening:** at the root ([Stage 1/my_player3.py:79-105](Stage 1/my_player3.py#L79-L105)), depths 1 through `min(self.max_depth, 24 - total_stones)` are searched in order, retaining the best move from the deepest completed iteration. Note `max_depth = 3` despite the README claiming 4.
- **Time control:** soft cap. `is_time_up()` returns true when more than `time_limit - 0.1 = 9.4 s` has elapsed since `get_move` started ([Stage 1/my_player3.py:338-339](Stage 1/my_player3.py#L338-L339)). Both the iterative-deepening loop and the inner `negamax` recursion check it. The check is advisory only — there is no hard kill, so a single slow leaf evaluation can still overrun.
- **Move ordering for alpha-beta:** at each node, `get_sorted_moves` ([Stage 1/my_player3.py:108-128](Stage 1/my_player3.py#L108-L128)) generates all legal moves, evaluates each with the one-ply heuristic, sorts by `(score desc, priority desc, center-distance asc)`, and returns the **top 8** (or **top 5** inside `negamax`, [Stage 1/my_player3.py:304](Stage 1/my_player3.py#L304)). This is a hard pruning of the move list, not just sorting — the agent never even considers the 9th-best one-ply move.

### 2.2 Heuristic

Three weight tables (`opening_weights`, `midgame_weights`, `endgame_weights`) keyed on stone count ([Stage 1/my_player3.py:17-44](Stage 1/my_player3.py#L17-L44), switched at counts 8 and 16). Each table weights six features:

| Feature | What it measures | Computed in |
| --- | --- | --- |
| `capture` | Number of opponent stones removed by the candidate move | `evaluate_move` ([Stage 1/my_player3.py:188](Stage 1/my_player3.py#L188)) |
| `liberty` | Liberties of the placed stone's group after the move | `find_liberties` ([Stage 1/my_player3.py:212](Stage 1/my_player3.py#L212)) |
| `territory` | BFS over reachable empties + ally / enemy stones, scored ±0.5 / +1 | `evaluate_territory` ([Stage 1/my_player3.py:231](Stage 1/my_player3.py#L231)) |
| `center` | 3.0 / 2.0 / 1.0 / 0 by Manhattan distance to (2,2) | `evaluate_position` ([Stage 1/my_player3.py:256](Stage 1/my_player3.py#L256)) |
| `connection` | Count of friendly neighbors at the placement | `state.detect_neighbor_ally` |
| `shape` | Flat bonus if the placement matches one of three small patterns | `forms_good_shape` ([Stage 1/my_player3.py:166](Stage 1/my_player3.py#L166)) |

The leaf evaluation `evaluate_board` ([Stage 1/my_player3.py:323-336](Stage 1/my_player3.py#L323-L336)) is **completely different** from the per-move heuristic: it just sums `±10 + liberties` per stone and ignores all the weight tables. This is a real inconsistency — moves are ordered by one heuristic and minimax leaves by another.

### 2.3 Opening book

`handle_opening` ([Stage 1/my_player3.py:266-285](Stage 1/my_player3.py#L266-L285)) only fires while `total_stones <= 4` (i.e. effectively the first 2-3 of our moves). It plays:
1. (2,2) on move 0,
2. a corner if the opponent already took the center,
3. otherwise the first available "strategic point" from the list `[(2,2), (1,1), (1,3), (3,1), (3,3), (0,2), (2,0), (2,4), (4,2)]`.

### 2.4 I/O

The agent runs once per move via the file-based protocol:

- `readInput(5)` reads `input.txt` → `(piece_type, previous_board, board)`,
- builds a `GO(5)` and `set_board(...)` (which infers `died_pieces` by diffing the two boards),
- calls `player.get_move(go, piece_type)` → `(row, col)` or `"PASS"`,
- `writeOutput(action)` writes `output.txt`.

There is **no in-process play loop** — every move spawns a fresh Python process and re-reads the entire board from disk. That is the single biggest reason this code is unsuitable for a multi-agent arena and must be the first thing we change.

## 3. Game engine — `host.GO` ([Stage 1/host.py](Stage 1/host.py))

### 3.1 State

- `board`: `n×n` list-of-lists, `0` empty / `1` black ("X") / `2` white ("O").
- `previous_board`: same shape, used for the **positional superko check**.
- `died_pieces`: stones removed on the previous move — required for the ko check and inferred from the board diff in `set_board`.
- `n_move`, `max_move = n*n - 1 = 24`, `komi = n/2 = 2.5`, `X_move` (whose turn), `verbose`.

### 3.2 Liberty / capture

`detect_neighbor` → `detect_neighbor_ally` → `ally_dfs` → `find_liberty` ([Stage 1/host.py:77-148](Stage 1/host.py#L77-L148)). `find_liberty` returns a **boolean** ("does this group have ≥1 liberty?"), not a count — fine for legality, but anything wanting a count (the agent's heuristic does) has to walk the group itself. `find_died_pieces` / `remove_died_pieces` ([Stage 1/host.py:150-180](Stage 1/host.py#L150-L180)) do a full board scan after every move.

### 3.3 Move legality (`valid_place_check`, [Stage 1/host.py:215-269](Stage 1/host.py#L215-L269))

In order:
1. In bounds, square empty.
2. Tentatively place. If the new group has a liberty → legal.
3. Otherwise remove the opponent's dead groups and re-check liberty. If it still has none → illegal (suicide).
4. Otherwise check positional superko: if `self.died_pieces` is non-empty **and** the resulting board equals `self.previous_board`, the move is illegal under the ko rule.

This is correct for the standard ko rule, but the suicide check has a subtle quirk: it forbids moves that *would* remove enemy stones to gain liberty if the resulting position is a ko repeat — so it's positional superko enforced only after a capture, which matches the textbook "simple ko" rule used in the assignment.

### 3.4 Move counter bug (intentional, but a trap)

`place_chess` ([Stage 1/host.py:194-213](Stage 1/host.py#L194-L213)) explicitly does **not** increment `self.n_move` — there's a comment `# Remove the following line for HW2 CS561 S2020`. Instead, `n_move` is passed in via `host.py -m $moves` from the bash harness. Inside the `GO.play(...)` driver ([Stage 1/host.py:347-408](Stage 1/host.py#L347-L408)), `n_move` *is* incremented manually at the bottom of the loop. This split is fragile and will not survive a programmatic API — Phase 1 needs a single source of truth.

### 3.5 Scoring

`score(piece_type)` is just stone count ([Stage 1/host.py:317-331](Stage 1/host.py#L317-L331)). `judge_winner` adds komi to white's score and returns 1 / 2 / 0 ([Stage 1/host.py:333-345](Stage 1/host.py#L333-L345)). This is **stone-count scoring, not area scoring**. Tromp-Taylor / Chinese area scoring (stones + surrounded empties) is what Phase 1 wants — the existing scoring under-counts territory and won't match standard implementations.

## 4. Bugs, dead code, and other issues

1. **`75.py` is dead.** Earlier checkpoint of the same agent. Delete in Phase 1.
2. **`evaluate_board` ignores the weight tables** ([Stage 1/my_player3.py:323](Stage 1/my_player3.py#L323)). Per-move and per-leaf heuristics disagree, which is silently bad for search quality. The refactored agent should pick one.
3. **`max_depth = 3` despite the README claiming 4** ([Stage 1/my_player3.py:9](Stage 1/my_player3.py#L9), [Readme.md:83](Readme.md#L83)).
4. **README lists weights `edge` and `corner`** that the agent does not use ([Readme.md:90-92](Readme.md#L90-L92)).
5. **Time control is soft.** A single slow leaf can blow past `time_limit`. The 0.1 s safety margin is too small for a hard 10 s budget.
6. **Move list pruning is severe.** `get_sorted_moves` returns top-8 at the root and `negamax` only looks at top-5 of those ([Stage 1/my_player3.py:128, 304](Stage 1/my_player3.py#L128)). On a 5×5 board with up to 25 candidate squares, this is an aggressive pre-pruning that the search cannot recover from.
7. **`copy_board` deep-copies the whole `GO` instance** ([Stage 1/host.py:68-75](Stage 1/host.py#L68-L75)). Called inside both `get_sorted_moves` and `negamax`, with another `place_chess` triggering yet another `deepcopy` of the previous board inside it. This is the dominant cost of the existing search and the single biggest perf win available — Phase 1 should switch to flat tuple/array board representations with cheap apply / undo.
8. **`evaluate_position` is hard-coded for a 5×5 board** ([Stage 1/my_player3.py:256-264](Stage 1/my_player3.py#L256-L264)) — uses literal `(2,2)`. Fine for now; flag it.
9. **`update_board(new_board)` is a no-op rebind**, not a copy ([Stage 1/host.py:271-278](Stage 1/host.py#L271-L278)). Easy to mistake for a defensive copy and introduce aliasing bugs.
10. **`n_move` is split between host driver, judge CLI, and the bash harness** (see §3.4). Will not survive an in-process API.
11. **Stone-count scoring, not area scoring** (see §3.5). Will under-count territory and disagree with every other Go implementation we benchmark against.
12. **No tests.** Nothing verifies capture, ko, suicide, or scoring. Given the engine bugs above, this is the highest-priority gap.
13. **`.DS_Store` is committed.** Add a `.gitignore`.
14. **Confusing color naming.** `host.py` says "X plays first" and the `play()` method validates that, but the README and most Go literature call black the first player and use B/W rather than X/O. The new engine should expose `Color.BLACK` / `Color.WHITE` and keep the integer encoding internal.

## 5. Refactor plan for Phase 1

Goal: the existing agent keeps playing identically, but it lives behind a clean `BaseAgent` interface and uses an in-process `Board` API instead of `input.txt` / `output.txt`. Everything downstream (greedy, minimax, AlphaZero, FastAPI, tournament) becomes possible.

### 5.1 New layout

Exactly the layout the brief specified:

```
go-arena/
├── engine/{board,rules,sgf,types}.py
├── agents/{base,random_agent,greedy_agent,minimax_agent,alphabeta_agent}.py
├── tournament/{match,round_robin,elo}.py
├── tests/
├── pyproject.toml
└── README.md
```

`Stage 1/` will be archived to `legacy/stage1/` (kept in-tree for reference, excluded from packaging) so the original CSCI 561 submission stays diffable.

### 5.2 Engine rewrite ([engine/](engine/))

- **`types.py`:** `Color` (enum, `BLACK = 1`, `WHITE = 2`, `EMPTY = 0`, `.opponent` property), `Move` (a sum of `Pass` and `Place(row, col)` — implemented as a dataclass with a sentinel for pass), `Position = tuple[int, int]`.
- **`board.py`:** an immutable-ish `Board` with `size`, a flat `tuple[int, ...]` for cheap hashing/copying, plus `previous_position_hash` for ko. Methods: `legal_moves(color)`, `play(move, color) -> Board` (returns a *new* board, never mutates), `is_terminal(consecutive_passes)`, `liberties_of(pos) -> frozenset[Position]`, `group_at(pos) -> frozenset[Position]`. The current `deepcopy(self)` cost goes away.
- **`rules.py`:** capture detection, suicide check, **positional superko** (using a hash of past positions, not just one previous board), area scoring (Chinese / Tromp-Taylor: stones + surrounded empties + komi). The legality semantics will match the original `valid_place_check` for non-ko cases — verified by a regression test that replays games against `host.py`.
- **`sgf.py`:** minimal SGF read/write for game replays. Useful for archive + the FastAPI download endpoint in Phase 2.

### 5.3 Agent interface ([agents/base.py](agents/base.py))

```python
class BaseAgent(ABC):
    name: str
    @abstractmethod
    def select_move(self, board: Board, color: Color, time_limit: float) -> Move: ...
    def reset(self) -> None: ...
```

Each agent is **stateless across games** unless it explicitly needs state (a TT or a network). `reset()` is called between games by the tournament runner.

### 5.4 Porting the existing agent → `agents/alphabeta_agent.py`

- Move the search and heuristic code over verbatim, then swap the calls onto the new `Board` API. The behavior must stay identical — that's verified by a regression test that replays a fixed seed against `RandomAgent` and asserts the move sequence matches the original `my_player3.py` driven through `host.py`.
- Resolve the per-move-vs-per-leaf heuristic mismatch (§4.2) by using the weighted heuristic at leaves too. Document this as an *intentional* deviation from the original in a docstring; the regression test gets a `# baseline` marker for the original behaviour and a parallel `# improved` test for the new one.
- Drop the file-based `main()`. Keep `max_depth=3` and `time_limit=9.5` as the defaults for behavior parity.

### 5.5 New agents

- `random_agent.py`: thin wrapper around `board.legal_moves(color)`.
- `greedy_agent.py`: picks the move with the best **one-ply** heuristic (capture + liberty + a small center bonus). No search.
- `minimax_agent.py`: depth-2 minimax, plain (no alpha-beta), same eval as `greedy`. Useful as the strict midpoint between `greedy` and `alphabeta`.

### 5.6 CLI

A single-entrypoint CLI lives in `go_arena/__main__.py`:

```
python -m go_arena play --black=alphabeta --white=greedy --time=2 --verbose
```

It instantiates both agents, runs them through a simple match loop (the same one tournament will use), prints the board after each move, and announces the result. No file I/O.

### 5.7 Tests ([tests/](tests/))

- `test_engine.py`: capture (single stone, group, multi-group), suicide forbidden except when it captures, ko (the canonical 4-stone ko shape), positional superko longer cycle, scoring with and without komi, liberty counts.
- `test_agents.py`: each of the 4 agents returns a legal move on (a) empty board, (b) a near-full board, (c) a board where pass is the only legal move.
- `test_regression.py`: `alphabeta` agent vs random with a fixed seed produces an exact pre-recorded move sequence — guards against accidental behavior drift.

Coverage target: >90% on `engine/`.

### 5.8 Tooling

- `pyproject.toml` with `ruff`, `pytest`, `pytest-cov`, `mypy --strict` on `engine/` and `agents/`.
- `.gitignore` (Python, `.DS_Store`, `.venv`, `__pycache__`).
- A pre-commit hook is overkill for now; CI in Phase 5.

### 5.9 Out of scope for Phase 1

FastAPI, React, AlphaZero, tournament runner with Elo, Docker. Those are Phases 2-5.

## 6. Summary

The existing project is a single-file negamax agent built around a CSCI 561 file-based judging harness. The agent's algorithm is sound (negamax + alpha-beta + iterative deepening + phase-aware heuristic + tiny opening book) but the code is unsuitable as a base for the arena because (a) the engine and agent are tangled together inside `host.py` and `my_player3.py`, (b) every move spawns a new process and re-reads the board from disk, (c) `deepcopy(self)` dominates search cost, (d) scoring is stone-count not area, and (e) there are no tests guarding any of it. Phase 1 fixes all five before adding anything new.

Stopping here for review.
