"""ASCII rendering smoke tests."""

from __future__ import annotations

from go_arena.engine.board import Board
from go_arena.engine.render import render_ascii
from go_arena.engine.rules import apply_move
from go_arena.engine.types import PASS, Color, Place, parse_move


def test_render_empty_board() -> None:
    out = render_ascii(Board.empty(5))
    lines = out.splitlines()
    # Header + 5 rows.
    assert len(lines) == 6
    assert lines[0].strip() == "A B C D E"
    assert lines[1].startswith(" 1")
    assert lines[5].startswith(" 5")


def test_render_with_stones() -> None:
    b = Board.empty(5)
    b = apply_move(b, Place(2, 2), Color.BLACK)
    b = apply_move(b, Place(0, 0), Color.WHITE)
    out = render_ascii(b)
    assert "X" in out
    assert "O" in out


def test_parse_move_pass() -> None:
    assert parse_move("PASS") is PASS
    assert parse_move("pass") is PASS


def test_parse_move_placement() -> None:
    m = parse_move("2,3")
    assert isinstance(m, Place)
    assert (m.row, m.col) == (2, 3)


def test_parse_move_with_space() -> None:
    m = parse_move("4 1")
    assert isinstance(m, Place)
    assert (m.row, m.col) == (4, 1)


def test_color_opponent_raises_on_empty() -> None:
    import pytest

    with pytest.raises(ValueError):
        _ = Color.EMPTY.opponent


def test_color_opponent_swaps() -> None:
    assert Color.BLACK.opponent is Color.WHITE
    assert Color.WHITE.opponent is Color.BLACK


def test_move_repr() -> None:
    assert repr(PASS) == "Pass"
    assert repr(Place(1, 2)) == "Place(1, 2)"
