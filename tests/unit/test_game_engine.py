from model.board import Board
from model.piece import Piece
from model.position import Position

from engine.game_engine import GameEngine


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