"""
Tests for PathChecker.find_last_free_cell()
"""

from model.board import Board
from model.piece import Piece
from model.position import Position
from realtime.move import Move
from rules.path_checker import PathChecker


def make_board(rows):
    return Board(rows)


def make_move(source, target, arrival_time, color="W"):
    """Helper: creates a move whose arrival_time equals the given value."""
    duration = arrival_time  # start=0 so arrival = duration
    return Move(Piece(color, "R"), source, target, 0, duration)


# ---------------------------------------------------------------------------
# Basic path — no obstacles
# ---------------------------------------------------------------------------

def test_returns_cell_just_before_blocked_when_clear():
    # source=(0,0), blocked=(0,4), path cells: (0,1),(0,2),(0,3)
    board = make_board([[None, None, None, None, None]])
    result = PathChecker.find_last_free_cell(
        Position(0, 0),
        Position(0, 4),
        board
    )
    assert result == Position(0, 3)


def test_returns_none_when_source_equals_blocked_neighbor():
    # source=(0,0), blocked=(0,1) — no intermediate cells
    board = make_board([[None, None]])
    result = PathChecker.find_last_free_cell(
        Position(0, 0),
        Position(0, 1),
        board
    )
    assert result is None


# ---------------------------------------------------------------------------
# Static obstacles on path
# ---------------------------------------------------------------------------

def test_skips_cell_occupied_by_static_piece():
    # path: (0,1) occupied, (0,2) free → returns (0,2)
    # Wait — scanning backwards: (0,2) first, (0,1) second.
    # (0,2) is free → returns (0,2)
    board = make_board([
        [None, Piece("B", "R"), None, None]
    ])
    result = PathChecker.find_last_free_cell(
        Position(0, 0),
        Position(0, 3),
        board
    )
    assert result == Position(0, 2)


def test_skips_multiple_occupied_cells():
    # path (0,1),(0,2),(0,3) — (0,2) and (0,3) occupied → returns (0,1)
    board = make_board([
        [None, None, Piece("B", "R"), Piece("B", "R"), None]
    ])
    result = PathChecker.find_last_free_cell(
        Position(0, 0),
        Position(0, 4),
        board
    )
    assert result == Position(0, 1)


def test_returns_none_when_all_cells_static_occupied():
    # path: (0,1),(0,2) both occupied
    board = make_board([
        [None, Piece("B", "R"), Piece("B", "R"), None]
    ])
    result = PathChecker.find_last_free_cell(
        Position(0, 0),
        Position(0, 3),
        board
    )
    assert result is None


# ---------------------------------------------------------------------------
# Dynamic obstacles (active_moves)
# ---------------------------------------------------------------------------

def test_skips_cell_targeted_by_earlier_arriving_move():
    # A move arrives at (0,2) at t=500, our piece arrives at t=1000
    # → (0,2) is occupied, returns (0,1)
    board = make_board([[None, None, None, None]])
    blocking = make_move(Position(1, 2), Position(0, 2), arrival_time=500)
    result = PathChecker.find_last_free_cell(
        Position(0, 0),
        Position(0, 3),
        board,
        active_moves=[blocking],
        arrival_time=1000
    )
    assert result == Position(0, 1)


def test_does_not_skip_cell_targeted_by_later_arriving_move():
    # A move arrives at (0,2) at t=2000, our piece arrives at t=1000
    # → (0,2) is NOT yet occupied → returns (0,2)
    board = make_board([[None, None, None, None]])
    later_move = make_move(Position(1, 2), Position(0, 2), arrival_time=2000)
    result = PathChecker.find_last_free_cell(
        Position(0, 0),
        Position(0, 3),
        board,
        active_moves=[later_move],
        arrival_time=1000
    )
    assert result == Position(0, 2)


def test_skips_cell_targeted_by_same_time_move():
    # Tie: a move arrives at exactly our arrival_time → treated as occupied
    board = make_board([[None, None, None, None]])
    tie_move = make_move(Position(1, 2), Position(0, 2), arrival_time=1000)
    result = PathChecker.find_last_free_cell(
        Position(0, 0),
        Position(0, 3),
        board,
        active_moves=[tie_move],
        arrival_time=1000
    )
    assert result == Position(0, 1)


def test_vertical_path():
    # Rook going up: source=(4,0), blocked=(0,0)
    # path: (3,0),(2,0),(1,0) — all clear
    board = make_board([
        [None],
        [None],
        [None],
        [None],
        [None],
    ])
    result = PathChecker.find_last_free_cell(
        Position(4, 0),
        Position(0, 0),
        board
    )
    assert result == Position(1, 0)


def test_returns_none_when_no_active_moves_and_only_source_between():
    # source=(0,0), blocked=(0,2), only (0,1) in path — (0,1) is free
    board = make_board([[None, None, None]])
    result = PathChecker.find_last_free_cell(
        Position(0, 0),
        Position(0, 2),
        board
    )
    assert result == Position(0, 1)
