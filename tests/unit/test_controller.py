from model.board import Board
from model.piece import Piece
from model.position import Position
from engine.game_engine import GameEngine
from input.board_mapper import BoardMapper
from input.board_rect import BoardRect
from input.controller import Controller
from session.local_session import LocalSession


def _controller(engine):
    mapper = BoardMapper(BoardRect(0, 0, 800, 800, 8, 8))
    return Controller(LocalSession(engine), mapper)


def test_click_selects_piece():
    engine = GameEngine(Board([[Piece("w", "R")]]))
    _controller(engine).click(50, 50)
    assert engine.get_selected() == Position(0, 0)


def test_click_empty_cell_does_not_select():
    engine = GameEngine(Board([[None]]))
    _controller(engine).click(50, 50)
    assert engine.get_selected() is None


def test_wait_delegates_to_the_engine():
    engine = GameEngine(Board([[None]]))
    _controller(engine).wait(100)
    assert not engine.is_game_over()


def test_jump_delegates_to_the_engine():
    engine = GameEngine(Board([[Piece("w", "P")]]))
    mapper = BoardMapper(BoardRect(0, 0, 800, 800, 8, 8))
    controller = Controller(LocalSession(engine), mapper)

    controller.jump(50, 50)

    assert engine.get_board().get(Position(0, 0)) is None
