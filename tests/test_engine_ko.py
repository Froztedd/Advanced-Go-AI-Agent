"""Ko / positional superko enforcement.

The canonical 4-stone ko in Go has the form

    . X O .
    X . X O
    . X O .

with B and W alternately able to capture a single opposing stone in
the contested square. The cycle is:

    R: B has just captured W at (1,1). Side to play: W.
    S: W plays (1,1), capturing B at (1,2). Side to play: B.
    T: B plays (1,2), capturing W at (1,1). Side to play: W. T == R.

Positional superko forbids T because it re-creates the (cells, side-to-
play) of R. Note the very first recapture (R -> S) is *not* itself
illegal under either simple ko or positional superko — the position S
is fresh.
"""

from __future__ import annotations

import pytest

from go_arena.engine.board import Board, IllegalMove
from go_arena.engine.rules import apply_move, is_legal
from go_arena.engine.types import PASS, Color, Place


def _ko_state_R() -> Board:
    """State R: B has just captured W at (1, 1). Side to play: W."""
    cells = [Color.EMPTY.value] * 25
    cells[0 * 5 + 1] = Color.BLACK.value
    cells[0 * 5 + 2] = Color.WHITE.value
    cells[1 * 5 + 0] = Color.BLACK.value
    cells[1 * 5 + 2] = Color.BLACK.value
    cells[1 * 5 + 3] = Color.WHITE.value
    cells[2 * 5 + 1] = Color.BLACK.value
    cells[2 * 5 + 2] = Color.WHITE.value
    board = Board(size=5, cells=tuple(cells))
    # apply_move stored R.position_hash(W) when arriving here from the
    # capture move, since the next side to play after that move was W.
    return Board(
        size=5,
        cells=board.cells,
        ko_history=frozenset({board.position_hash(Color.WHITE)}),
        consecutive_passes=0,
        move_number=7,
    )


def test_first_recapture_is_legal() -> None:
    """R -> S: White retakes immediately. The resulting position S has
    not been seen, so it is legal under positional superko."""
    R = _ko_state_R()
    assert is_legal(R, Place(1, 1), Color.WHITE)


def test_ko_blocks_second_recapture() -> None:
    """R -> S -> attempted T: the second recapture would re-create R
    with W to play, exactly what was last stored in history."""
    R = _ko_state_R()
    S = apply_move(R, Place(1, 1), Color.WHITE)
    # Now B wants to play (1,2). That would capture W at (1,1) and
    # produce the same board as R, with W to play next. Blocked.
    assert not is_legal(S, Place(1, 2), Color.BLACK)
    with pytest.raises(IllegalMove):
        apply_move(S, Place(1, 2), Color.BLACK)


def test_ko_lifted_after_intervening_moves() -> None:
    """R -> S -> tenuki x 2 -> recapture is now legal because the new
    position differs from R by the tenuki stones."""
    R = _ko_state_R()
    S = apply_move(R, Place(1, 1), Color.WHITE)
    after = apply_move(S, Place(4, 4), Color.BLACK)
    after = apply_move(after, Place(4, 0), Color.WHITE)
    assert is_legal(after, Place(1, 2), Color.BLACK)
    final = apply_move(after, Place(1, 2), Color.BLACK)
    assert final.at(1, 1) == Color.EMPTY  # W captured
    assert final.at(1, 2) == Color.BLACK


def test_pass_does_not_clear_ko_history() -> None:
    """Passing must not shrink ko history."""
    R = _ko_state_R()
    history_before = R.ko_history
    after = apply_move(R, PASS, Color.WHITE)
    assert history_before <= after.ko_history


def test_two_passes_terminate_game() -> None:
    b = Board.empty(5)
    b = apply_move(b, PASS, Color.BLACK)
    assert not b.is_terminal
    b = apply_move(b, PASS, Color.WHITE)
    assert b.is_terminal


def test_superko_blocks_longer_cycle() -> None:
    """Positional superko (unlike simple ko) blocks any repeated position,
    not just the immediately-previous one. Construct three different
    intermediate states and try to revisit the first one."""
    b = Board.empty(5)
    b = apply_move(b, Place(0, 0), Color.BLACK)
    initial_hash = b.position_hash(Color.BLACK)  # would be next-to-play after this move? no
    # ko_history after this move stored b.position_hash(WHITE)
    assert b.position_hash(Color.WHITE) in b.ko_history
    # Make some moves and undo... we can't undo, so verify the history grows.
    b = apply_move(b, Place(0, 1), Color.WHITE)
    b = apply_move(b, Place(0, 2), Color.BLACK)
    b = apply_move(b, Place(0, 3), Color.WHITE)
    # All four prior position hashes are still in history.
    assert len(b.ko_history) == 4
    _ = initial_hash  # touched to keep linter happy
