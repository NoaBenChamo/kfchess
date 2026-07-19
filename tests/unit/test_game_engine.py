from model.board import Board
from model.piece import Piece
from model.position import Position

from engine.game_engine import GameEngine
from realtime.move import Move


def test_initial_state():

    board = Board([
        [None]
    ])

    engine = GameEngine(board)

    assert engine.get_board() == board
    assert engine.get_selected() is None
    assert not engine.is_game_over()


def test_select_piece():

    board = Board([
        [Piece("W", "R")]
    ])

    engine = GameEngine(board)

    pos = Position(0, 0)

    engine.select(pos)

    assert engine.get_selected() == pos


def test_select_empty_square():

    board = Board([
        [None]
    ])

    engine = GameEngine(board)

    engine.select(Position(0, 0))

    assert engine.get_selected() is None


def test_select_outside_board():

    board = Board([
        [None]
    ])

    engine = GameEngine(board)

    engine.select(Position(5, 5))

    assert engine.get_selected() is None


def test_set_game_over():

    board = Board([
        [None]
    ])

    engine = GameEngine(board)

    engine.set_game_over()

    assert engine.is_game_over()


def test_cannot_select_after_game_over():

    board = Board([
        [Piece("W", "R")]
    ])

    engine = GameEngine(board)

    engine.set_game_over()

    engine.select(Position(0, 0))

    assert engine.get_selected() is None


def test_wait_without_moves():

    board = Board([
        [None]
    ])

    engine = GameEngine(board)

    engine.wait(500)

    assert not engine.is_game_over()


def test_move_request_without_selection():

    board = Board([
        [Piece("W", "R"), None]
    ])

    engine = GameEngine(board)

    engine.move_request(Position(0, 1))

    assert engine.get_selected() is None


def test_pawn_that_captures_king_is_not_promoted_after_game_over():
    pawn = Piece("w", "P")
    board = Board([
        [Piece("b", "K")],
        [pawn],
    ])
    engine = GameEngine(board)
    engine._arbiter.add_move(Move(
        pawn,
        Position(1, 0),
        Position(0, 0),
        start_time=0,
        duration=100,
    ))

    engine.tick(100)

    assert engine.is_game_over()
    assert board.get(Position(0, 0)) is pawn
    assert pawn.type == "P"


def test_pawn_still_promotes_after_a_regular_move_to_the_last_rank():
    pawn = Piece("w", "P")
    board = Board([
        [None],
        [pawn],
    ])
    engine = GameEngine(board)
    engine._arbiter.add_move(Move(
        pawn,
        Position(1, 0),
        Position(0, 0),
        start_time=0,
        duration=100,
    ))

    engine.tick(100)

    assert not engine.is_game_over()
    assert pawn.type == "Q"
