from model.board import Board
from model.piece import Piece
from model.position import Position

from realtime.move import Move
from realtime.real_time_arbiter import RealTimeArbiter


def test_add_move():

    board = Board([
        [Piece("W", "R"), None]
    ])

    arbiter = RealTimeArbiter(board)

    move = Move(
        Piece("W", "R"),
        Position(0, 0),
        Position(0, 1),
        0,
        100
    )

    arbiter.add_move(move)

    assert len(arbiter._active_moves) == 1


def test_wait_does_not_finish_move_too_early():

    board = Board([
        [Piece("W", "R"), None]
    ])

    arbiter = RealTimeArbiter(board)

    move = Move(
        Piece("W", "R"),
        Position(0, 0),
        Position(0, 1),
        0,
        100
    )

    arbiter.add_move(move)

    arbiter.wait(50)

    assert len(arbiter._active_moves) == 1


def test_wait_finishes_move():

    board = Board([
        [Piece("W", "R"), None]
    ])

    arbiter = RealTimeArbiter(board)

    move = Move(
        Piece("W", "R"),
        Position(0, 0),
        Position(0, 1),
        0,
        100
    )

    arbiter.add_move(move)

    arbiter.wait(100)

    assert len(arbiter._active_moves) == 0


def test_clock_advances():

    board = Board([
        [None]
    ])

    arbiter = RealTimeArbiter(board)

    arbiter.wait(250)

    assert arbiter.get_time() == 250


def test_get_events_returns_empty_when_no_events():

    board = Board([
        [None]
    ])

    arbiter = RealTimeArbiter(board)

    assert arbiter.get_events() == []


def test_events_are_cleared_after_read():

    board = Board([
        [None]
    ])

    arbiter = RealTimeArbiter(board)

    arbiter._game_events.append("GAME_OVER")

    assert arbiter.get_events() == ["GAME_OVER"]

    assert arbiter.get_events() == []


def test_is_moving_before_finish():

    board = Board([
        [Piece("W", "R"), None]
    ])

    arbiter = RealTimeArbiter(board)

    move = Move(
        Piece("W", "R"),
        Position(0, 0),
        Position(0, 1),
        0,
        100
    )

    arbiter.add_move(move)

    assert arbiter.is_moving(Position(0, 0))


def test_is_not_moving_after_finish():

    board = Board([
        [Piece("W", "R"), None]
    ])

    arbiter = RealTimeArbiter(board)

    move = Move(
        Piece("W", "R"),
        Position(0, 0),
        Position(0, 1),
        0,
        100
    )

    arbiter.add_move(move)

    arbiter.wait(100)

    assert not arbiter.is_moving(Position(0, 0))