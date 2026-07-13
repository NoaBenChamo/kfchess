"""
Tests for Move.get_path(), position_at(), time_at(), and move_id.
"""

import pytest

from model.piece import Piece
from model.position import Position
from realtime.move import Move


def make_rook_move(source, target, start=0, duration=1000):
    return Move(Piece("W", "R"), source, target, start, duration)


# ---------------------------------------------------------------------------
# get_path
# ---------------------------------------------------------------------------

def test_get_path_horizontal():
    move = make_rook_move(Position(0, 0), Position(0, 3))
    path = move.get_path()
    assert path == [
        Position(0, 1),
        Position(0, 2),
        Position(0, 3),
    ]


def test_get_path_vertical():
    move = make_rook_move(Position(0, 0), Position(3, 0))
    path = move.get_path()
    assert path == [
        Position(1, 0),
        Position(2, 0),
        Position(3, 0),
    ]


def test_get_path_single_step():
    move = make_rook_move(Position(0, 0), Position(0, 1))
    path = move.get_path()
    assert path == [Position(0, 1)]


def test_get_path_does_not_include_source():
    move = make_rook_move(Position(2, 2), Position(2, 5))
    path = move.get_path()
    assert Position(2, 2) not in path


def test_get_path_includes_target():
    move = make_rook_move(Position(0, 0), Position(0, 4))
    path = move.get_path()
    assert path[-1] == Position(0, 4)


# ---------------------------------------------------------------------------
# position_at
# ---------------------------------------------------------------------------

def test_position_at_start_returns_source():
    move = make_rook_move(Position(0, 0), Position(0, 4), start=0, duration=1000)
    assert move.position_at(0) == Position(0, 0)


def test_position_at_before_start_returns_source():
    move = make_rook_move(Position(0, 0), Position(0, 4), start=500, duration=1000)
    assert move.position_at(0) == Position(0, 0)


def test_position_at_arrival_returns_target():
    move = make_rook_move(Position(0, 0), Position(0, 4), start=0, duration=1000)
    assert move.position_at(1000) == Position(0, 4)


def test_position_at_after_arrival_returns_target():
    move = make_rook_move(Position(0, 0), Position(0, 4), start=0, duration=1000)
    assert move.position_at(9999) == Position(0, 4)


def test_position_at_midpoint():
    # Rook e1 -> e8: 7 steps (rows 7 -> 0, col 4 fixed)
    # path: row 6,5,4,3,2,1,0 (col 4 throughout)
    move = Move(
        Piece("W", "R"),
        Position(7, 4),  # e1
        Position(0, 4),  # e8
        start_time=0,
        duration=7000
    )
    # At t=3500 (halfway), step_index = int(0.5 * 7) = 3
    # path[3] = Position(3, 4)  which is e5
    assert move.position_at(3500) == Position(3, 4)


# ---------------------------------------------------------------------------
# time_at
# ---------------------------------------------------------------------------

def test_time_at_source_returns_start_time():
    move = make_rook_move(Position(0, 0), Position(0, 4), start=0, duration=1000)
    assert move.time_at(Position(0, 0)) == 0


def test_time_at_target_returns_arrival_time():
    move = make_rook_move(Position(0, 0), Position(0, 4), start=0, duration=1000)
    # path has 4 cells; last cell (index 3) -> time = int(0 + 4/4 * 1000) = 1000
    assert move.time_at(Position(0, 4)) == 1000


def test_time_at_intermediate_cell():
    # 4-step horizontal move, duration=1000
    # path: (0,1),(0,2),(0,3),(0,4)
    # cell (0,2) is index 1 -> time = int(0 + 2/4 * 1000) = 500
    move = make_rook_move(Position(0, 0), Position(0, 4), start=0, duration=1000)
    assert move.time_at(Position(0, 2)) == 500


def test_time_at_cell_not_on_path_returns_none():
    move = make_rook_move(Position(0, 0), Position(0, 4), start=0, duration=1000)
    assert move.time_at(Position(5, 5)) is None


def test_time_at_cell_off_column_returns_none():
    move = make_rook_move(Position(0, 0), Position(0, 4), start=0, duration=1000)
    assert move.time_at(Position(0, 7)) is None


# ---------------------------------------------------------------------------
# move_id
# ---------------------------------------------------------------------------

def test_move_ids_are_unique():
    m1 = make_rook_move(Position(0, 0), Position(0, 1))
    m2 = make_rook_move(Position(1, 0), Position(1, 1))
    assert m1.move_id != m2.move_id


def test_move_ids_are_increasing():
    m1 = make_rook_move(Position(0, 0), Position(0, 1))
    m2 = make_rook_move(Position(1, 0), Position(1, 1))
    assert m2.move_id > m1.move_id
