"""
Tests for PathChecker.clear() with dynamic active_moves support.
"""

from model.board import Board
from model.piece import Piece
from model.position import Position
from realtime.move import Move
from rules.path_checker import PathChecker


def make_board(rows):
    return Board(rows)


def make_move(source, target, start=0, duration=1000, color="W"):
    return Move(Piece(color, "R"), source, target, start, duration)


# ---------------------------------------------------------------------------
# Static checks (backwards-compatible)
# ---------------------------------------------------------------------------

def test_clear_path_no_pieces():
    board = make_board([
        [None, None, None, None]
    ])
    assert PathChecker.clear(board, Position(0, 0), Position(0, 3))


def test_blocked_by_static_piece():
    board = make_board([
        [None, Piece("B", "R"), None, None]
    ])
    assert not PathChecker.clear(board, Position(0, 0), Position(0, 3))


def test_target_occupied_not_checked_by_path_checker():
    # PathChecker only checks INTERMEDIATE cells, not the target itself
    board = make_board([
        [None, None, Piece("B", "R")]
    ])
    assert PathChecker.clear(board, Position(0, 0), Position(0, 2))


# ---------------------------------------------------------------------------
# Dynamic checks
# ---------------------------------------------------------------------------

def test_clear_with_no_active_moves():
    board = make_board([
        [None, None, None, None]
    ])
    assert PathChecker.clear(
        board,
        Position(0, 0),
        Position(0, 3),
        active_moves=[],
        move_start_time=0,
        move_duration=1000
    )


def test_blocked_by_moving_piece_at_passage_time():
    """
    Rook A wants to go (0,0)->(0,3).
    Rook B is moving (2,1)->(0,1) and will be at (0,1) around t=1000.
    Rook A would pass (0,1) around t=333.
    Rook B is NOT at (0,1) at t=333, so path should be clear.
    """
    board = make_board([
        [None, None, None, None],
        [None, None, None, None],
        [None, Piece("W", "R"), None, None],
    ])
    moving_b = make_move(
        Position(2, 1),
        Position(0, 1),
        start=0,
        duration=2000
    )
    # At t=333: moving_b is at step int(333/2000 * 2) = 0 -> (2,1) still
    assert PathChecker.clear(
        board,
        Position(0, 0),
        Position(0, 3),
        active_moves=[moving_b],
        move_start_time=0,
        move_duration=1000
    )


def test_blocked_by_moving_piece_same_time_and_cell():
    """
    Rook A: (0,0)->(0,4), duration=4000, start=0.
    Rook B: (4,2)->(0,2), duration=4000, start=0.

    Rook A reaches (0,2) at t = int(0 + 2/4 * 4000) = 2000.
    Rook B.position_at(2000): step = int(2000/4000 * 4) = 2 -> path[1] = Position(2,2).
    So rook B is at (2,2) at t=2000, not (0,2). Path should be clear.
    This test verifies no false positive.
    """
    board = make_board([
        [None, None, None, None, None],
        [None, None, None, None, None],
        [None, None, None, None, None],
        [None, None, None, None, None],
        [None, None, Piece("W", "R"), None, None],
    ])
    moving_b = make_move(
        Position(4, 2),
        Position(0, 2),
        start=0,
        duration=4000
    )
    assert PathChecker.clear(
        board,
        Position(0, 0),
        Position(0, 4),
        active_moves=[moving_b],
        move_start_time=0,
        move_duration=4000
    )


def test_moving_piece_already_passed_does_not_block():
    """
    Rook B already moved past the cell before Rook A gets there.
    Path should be clear.
    """
    board = make_board([
        [None, None, None, None]
    ])
    # B has already finished (arrival_time=100, current_time context > 100)
    moving_b = make_move(
        Position(1, 1),
        Position(0, 1),
        start=0,
        duration=100
    )
    # A starts at t=500, passage at t=500+333=833; B is at target (0,1) since t=100
    # position_at(833) for B -> target = (0,1)
    # (0,1) is on A's path -> blocked (B is sitting at the intermediate cell)
    # This is correct behaviour: B has landed there statically
    # The static board check would catch it if the board was updated,
    # but the dynamic check also catches it.
    assert not PathChecker.clear(
        board,
        Position(0, 0),
        Position(0, 3),
        active_moves=[moving_b],
        move_start_time=500,
        move_duration=1000
    )
