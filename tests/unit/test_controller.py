from model.board import Board
from model.piece import Piece
from model.position import Position

from engine.game_engine import GameEngine
from input.controller import Controller


def test_click_selects_piece():

    board = Board([
        [Piece("W", "R"), None]
    ])

    engine = GameEngine(board)

    controller = Controller(engine)

    controller.click(
        50,
        50
    )

    assert engine.get_selected() == Position(0, 0)



def test_click_empty_cell():

    board = Board([
        [None]
    ])

    engine = GameEngine(board)

    controller = Controller(engine)

    controller.click(
        50,
        50
    )

    assert engine.get_selected() is None



def test_click_converts_pixels_to_position():

    board = Board([
        [None, None],
        [None, Piece("W", "R")]
    ])

    engine = GameEngine(board)

    controller = Controller(engine)

    controller.click(
        150,
        150
    )

    assert engine.get_selected() == Position(1, 1)



def test_wait_calls_engine():

    board = Board([
        [None]
    ])

    engine = GameEngine(board)

    controller = Controller(engine)

    controller.wait(100)

    assert not engine.is_game_over()



def test_get_board():

    board = Board([
        [None]
    ])

    engine = GameEngine(board)

    controller = Controller(engine)

    assert controller.get_board() == board