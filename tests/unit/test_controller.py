from model.board import Board
from model.piece import Piece
from model.position import Position
from engine.game_engine import GameEngine
from input.board_mapper import BoardMapper
from input.board_rect import BoardRect
from input.controller import Controller


def test_click_selects_piece():
    engine = GameEngine(Board([[Piece("w", "R")]]))
    mapper = BoardMapper(BoardRect(0, 0, 800, 800, 8, 8))
    Controller(engine, mapper).click(50, 50)
    assert engine.get_selected() == Position(0, 0)


def test_click_empty_cell_does_not_select():
    engine = GameEngine(Board([[None]]))
    mapper = BoardMapper(BoardRect(0, 0, 800, 800, 8, 8))
    Controller(engine, mapper).click(50, 50)
    assert engine.get_selected() is None


def test_wait_delegates_to_the_engine():
    engine = GameEngine(Board([[None]]))
    mapper = BoardMapper(BoardRect(0, 0, 800, 800, 8, 8))
    Controller(engine, mapper).wait(100)
    assert not engine.is_game_over()
