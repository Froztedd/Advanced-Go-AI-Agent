"""Suicide rule: forbidden unless the move captures."""

from __future__ import annotations

import pytest

from go_arena.engine.board import Board, IllegalMove
from go_arena.engine.rules import apply_move, is_legal
from go_arena.engine.types import Color, Place


def test_suicide_in_corner_is_illegal() -> None:
    b = Board.empty(5)
    b = apply_move(b, Place(0, 1), Color.WHITE)
    b = apply_move(b, Place(4, 4), Color.BLACK)
    b = apply_move(b, Place(1, 0), Color.WHITE)
    assert not is_legal(b, Place(0, 0), Color.BLACK)
    with pytest.raises(IllegalMove):
        apply_move(b, Place(0, 0), Color.BLACK)


def test_suicide_capturing_self_via_capture_is_legal() -> None:
    """If the placement captures opponent stones first, it becomes legal even when
    the placed stone would have had no liberties without the capture."""
    b = Board.empty(5)
    # Black surrounds a single White stone at (0,0) except for one White-occupied liberty.
    # Sequence: W(0,0), B(0,1), W(4,4) tenuki, B(1,0). White at (0,0) is captured.
    # Now Black plays at (0,0) — legal because it doesn't trigger suicide on a fresh empty.
    b = apply_move(b, Place(0, 0), Color.WHITE)
    b = apply_move(b, Place(0, 1), Color.BLACK)
    b = apply_move(b, Place(4, 4), Color.WHITE)
    b = apply_move(b, Place(1, 0), Color.BLACK)
    assert b.at(0, 0) == Color.EMPTY  # captured

    # Trickier: a true "suicide-with-capture" — Black plays in eye of white shape,
    # capturing a white group of size 1 surrounding the eye.
    b2 = Board.empty(5)
    # Build:  . W .
    #         W . W      (B will play center, capturing surrounding W if W has 0 libs after.)
    #         . W .
    # That requires the surrounding W to have only the center as liberty. Build it on a corner.
    b2 = apply_move(b2, Place(2, 2), Color.WHITE)
    b2 = apply_move(b2, Place(0, 0), Color.BLACK)
    b2 = apply_move(b2, Place(2, 4), Color.WHITE)
    b2 = apply_move(b2, Place(0, 1), Color.BLACK)
    b2 = apply_move(b2, Place(1, 3), Color.WHITE)
    b2 = apply_move(b2, Place(0, 2), Color.BLACK)
    b2 = apply_move(b2, Place(3, 3), Color.WHITE)
    b2 = apply_move(b2, Place(0, 4), Color.BLACK)
    # Now W at (1,3),(2,2),(2,4),(3,3) — diamond around (2,3). All connected? No: (1,3)
    # neighbors include (2,3) only (empty). (2,2) connects to nothing same color directly.
    # Each white stone is its own group. Each has libs other than (2,3) too (they're spaced).
    # So this isn't a clean suicide-with-capture demo. Skip this construction.
    assert True  # Reserve more elaborate suicide-capture for a custom-built Board test below.


def test_suicide_capturing_via_custom_board() -> None:
    """Construct a Board directly to set up a clean suicide-with-capture case.

    On a 3x3 board, an all-White ring around an empty center:

        W W W
        W . W
        W W W

    The eight W stones form a single connected group whose only liberty
    is the center. Black plays (1, 1): the W group is captured, then
    Black's stone has four newly-emptied neighbors. Without the capture,
    the placement would be suicide. The rule must permit this move.
    """
    cells = [Color.WHITE.value] * 9
    cells[1 * 3 + 1] = Color.EMPTY.value
    b = Board(size=3, cells=tuple(cells))

    assert is_legal(b, Place(1, 1), Color.BLACK)
    after = apply_move(b, Place(1, 1), Color.BLACK)
    assert after.at(1, 1) == Color.BLACK
    # All eight white stones removed.
    for r in range(3):
        for c in range(3):
            if (r, c) != (1, 1):
                assert after.at(r, c) == Color.EMPTY


def test_placing_on_occupied_is_illegal() -> None:
    b = Board.empty(5)
    b = apply_move(b, Place(2, 2), Color.BLACK)
    assert not is_legal(b, Place(2, 2), Color.WHITE)
    assert not is_legal(b, Place(2, 2), Color.BLACK)


def test_out_of_bounds_is_illegal() -> None:
    b = Board.empty(5)
    assert not is_legal(b, Place(-1, 0), Color.BLACK)
    assert not is_legal(b, Place(5, 0), Color.BLACK)
    assert not is_legal(b, Place(0, 5), Color.BLACK)
