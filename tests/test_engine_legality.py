"""legal_moves correctness and group / liberty utilities."""

from __future__ import annotations

from go_arena.engine.board import Board
from go_arena.engine.rules import apply_move
from go_arena.engine.types import PASS, Color, Place


def test_legal_moves_on_empty_board_is_25_plus_pass() -> None:
    b = Board.empty(5)
    moves = b.legal_moves(Color.BLACK)
    assert PASS in moves
    placements = [m for m in moves if isinstance(m, Place)]
    assert len(placements) == 25


def test_legal_moves_excludes_occupied_squares() -> None:
    b = Board.empty(5)
    b = apply_move(b, Place(2, 2), Color.BLACK)
    moves = b.legal_moves(Color.WHITE)
    placements = {(m.row, m.col) for m in moves if isinstance(m, Place)}
    assert (2, 2) not in placements


def test_pass_is_always_legal() -> None:
    b = Board.empty(5)
    assert PASS in b.legal_moves(Color.BLACK)
    assert PASS in b.legal_moves(Color.WHITE)
    # Even after several moves.
    b = apply_move(b, Place(2, 2), Color.BLACK)
    b = apply_move(b, Place(0, 0), Color.WHITE)
    assert PASS in b.legal_moves(Color.BLACK)


def test_group_at_returns_connected_stones_only() -> None:
    b = Board.empty(5)
    b = apply_move(b, Place(0, 0), Color.BLACK)
    b = apply_move(b, Place(4, 4), Color.WHITE)
    b = apply_move(b, Place(0, 1), Color.BLACK)
    b = apply_move(b, Place(4, 3), Color.WHITE)
    b = apply_move(b, Place(2, 2), Color.BLACK)  # disconnected
    g = b.group_at((0, 0))
    assert g == frozenset({(0, 0), (0, 1)})
    g2 = b.group_at((2, 2))
    assert g2 == frozenset({(2, 2)})


def test_group_at_empty_returns_empty_set() -> None:
    b = Board.empty(5)
    assert b.group_at((0, 0)) == frozenset()


def test_liberties_of_empty_returns_empty_set() -> None:
    b = Board.empty(5)
    assert b.liberties_of((0, 0)) == frozenset()


def test_liberties_of_corner_stone() -> None:
    b = Board.empty(5)
    b = apply_move(b, Place(0, 0), Color.BLACK)
    libs = b.liberties_of((0, 0))
    assert libs == frozenset({(0, 1), (1, 0)})


def test_neighbors_handles_corners_and_edges() -> None:
    b = Board.empty(5)
    assert set(b.neighbors(0, 0)) == {(0, 1), (1, 0)}
    assert set(b.neighbors(4, 4)) == {(4, 3), (3, 4)}
    assert set(b.neighbors(2, 2)) == {(1, 2), (3, 2), (2, 1), (2, 3)}


def test_str_renders_board() -> None:
    b = Board.empty(3)
    assert str(b) == ". . .\n. . .\n. . ."


def test_position_hash_includes_color_to_play() -> None:
    b = Board.empty(5)
    h_black = b.position_hash(Color.BLACK)
    h_white = b.position_hash(Color.WHITE)
    assert h_black != h_white


def test_with_stone_low_level_does_not_check_legality() -> None:
    """``with_stone`` is a low-level helper; it does not enforce rules."""
    b = Board.empty(5)
    b = b.with_stone(0, 0, Color.BLACK)
    # Overwriting is allowed at this level.
    b = b.with_stone(0, 0, Color.WHITE)
    assert b.at(0, 0) == Color.WHITE
