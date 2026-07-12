from model.board import Board
from model.piece import Piece
from model.position import Position

from engine.game_engine import GameEngine


def test_full_move_flow():

    board = Board([
        [
            Piece("W", "R"),
            None
        ]
    ])

    game = GameEngine(board)

    source = Position(0, 0)
    target = Position(0, 1)

    # בחירת כלי
    game.select(source)

    assert game.get_selected() == source

    # בקשת תנועה
    game.move_request(target)

    # התנועה עדיין לא הסתיימה
    assert board.get(source) is not None
    assert board.get(target) is None

    # מקדמים זמן
    game.wait(1000)

    # הכלי הגיע ליעד
    assert board.get(source) is None
    assert board.get(target) is not None


def test_game_over_state():

    board = Board([
        [
            Piece("W", "R"),
            Piece("B", "K")
        ]
    ])

    game = GameEngine(board)

    game.set_game_over()

    assert game.is_game_over()