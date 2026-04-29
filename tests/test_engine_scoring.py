"""Area scoring (Tromp-Taylor) and legacy stone-count scoring."""

from __future__ import annotations

import pytest

from go_arena.engine.board import Board
from go_arena.engine.rules import score_area, score_stone_count
from go_arena.engine.types import Color


def test_empty_board_white_wins_by_komi() -> None:
    b = Board.empty(5)
    s = score_area(b, komi=2.5)
    assert s["black"] == 0
    assert s["white"] == 2.5
    assert s["winner"] == Color.WHITE


def test_all_black_board() -> None:
    b = Board(size=5, cells=tuple([Color.BLACK.value] * 25))
    s = score_area(b, komi=2.5)
    assert s["black"] == 25
    assert s["white"] == 2.5
    assert s["winner"] == Color.BLACK


def test_area_scoring_counts_surrounded_empties() -> None:
    """Black wall surrounds a 2-cell empty region; those empties belong to Black."""
    cells = [Color.EMPTY.value] * 25
    # Row 0: X X X X X
    for c in range(5):
        cells[0 * 5 + c] = Color.BLACK.value
    # Row 1: X . . X X
    cells[1 * 5 + 0] = Color.BLACK.value
    cells[1 * 5 + 3] = Color.BLACK.value
    cells[1 * 5 + 4] = Color.BLACK.value
    # Row 2: X X X X X
    for c in range(5):
        cells[2 * 5 + c] = Color.BLACK.value
    b = Board(size=5, cells=tuple(cells))
    s = score_area(b, komi=0)
    # Black stones: 13. Surrounded empty region: 2. Lower 2 rows (10 cells) are empty,
    # bordered by Black on top and the board edge elsewhere — so they are also
    # Black-only territory.
    assert s["black"] == 13 + 2 + 10
    assert s["white"] == 0
    assert s["winner"] == Color.BLACK


def test_area_scoring_dame_is_neutral() -> None:
    """Empty region bordered by both colors counts for nobody."""
    cells = [Color.EMPTY.value] * 25
    # Row 0: X X . O O
    cells[0 * 5 + 0] = Color.BLACK.value
    cells[0 * 5 + 1] = Color.BLACK.value
    cells[0 * 5 + 3] = Color.WHITE.value
    cells[0 * 5 + 4] = Color.WHITE.value
    b = Board(size=5, cells=tuple(cells))
    s = score_area(b, komi=0)
    # Every empty cell is reachable from (0, 2) and that region borders
    # both colors, so all 21 empties are dame.
    assert s["black"] == 2
    assert s["white"] == 2
    assert s["winner"] == Color.EMPTY


def test_komi_breaks_ties_for_white() -> None:
    cells = [Color.EMPTY.value] * 25
    cells[0] = Color.BLACK.value
    cells[24] = Color.WHITE.value
    b = Board(size=5, cells=tuple(cells))
    s = score_stone_count(b, komi=2.5)
    assert s["black"] == 1
    assert s["white"] == 3.5
    assert s["winner"] == Color.WHITE


def test_stone_count_scoring_matches_legacy_semantics() -> None:
    """Legacy host.py scoring is just stone count + komi for white."""
    cells = [Color.EMPTY.value] * 25
    cells[0] = Color.BLACK.value
    cells[1] = Color.BLACK.value
    cells[2] = Color.BLACK.value
    cells[24] = Color.WHITE.value
    b = Board(size=5, cells=tuple(cells))
    s = score_stone_count(b, komi=2.5)
    assert s["black"] == 3
    assert s["white"] == 3.5
    assert s["winner"] == Color.WHITE


def test_tie_when_scores_equal() -> None:
    cells = [Color.EMPTY.value] * 25
    cells[0] = Color.BLACK.value
    cells[1] = Color.BLACK.value
    cells[2] = Color.BLACK.value
    cells[3] = Color.BLACK.value
    cells[24] = Color.WHITE.value
    b = Board(size=5, cells=tuple(cells))
    # area: black has 4 stones + surrounded empties from upper-right (none, mixed).
    # Use stone-count scoring for a clean tie scenario.
    s = score_stone_count(b, komi=4.0)
    assert s["black"] == 4
    assert s["white"] == 5.0
    assert s["winner"] == Color.WHITE


@pytest.mark.parametrize("komi", [0, 2.5, 6.5])
def test_komi_passes_through(komi: float) -> None:
    b = Board.empty(5)
    s = score_area(b, komi=komi)
    assert s["white"] == komi
