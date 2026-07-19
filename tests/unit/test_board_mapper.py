from model.board import Board
from model.piece import Piece
from model.position import Position
from engine.game_engine import GameEngine
from input.board_mapper import BoardMapper
from input.board_rect import BoardRect
from input.controller import Controller
from model.piece_state import PieceState


def create_mapper(x=160, y=40, width=800, height=800):
    return BoardMapper(BoardRect(x, y, width, height, 8, 8))


def test_board_rect_contains_its_edges_only_on_the_inside():
    rect = BoardRect(100, 50, 800, 800, 8, 8)
    assert rect.contains(100, 50)
    assert rect.contains(899, 849)
    assert not rect.contains(900, 849)
    assert not rect.contains(899, 850)


def test_mapper_converts_window_pixels_to_positions():
    mapper = create_mapper()
    assert mapper.to_position(160, 40) == Position(0, 0)
    assert mapper.to_position(959, 839) == Position(7, 7)
    assert mapper.to_position(159, 40) is None
    assert mapper.to_position(160, 840) is None


def test_mapper_round_trips_every_cell():
    mapper = create_mapper(200, 100)
    for row in range(8):
        for col in range(8):
            position = Position(row, col)
            assert mapper.to_position(*mapper.to_pixels(position)) == position


def test_mapper_owns_its_rect_without_global_state():
    first = create_mapper(0, 0)
    second = create_mapper(160, 40)
    assert first.to_position(0, 0) == Position(0, 0)
    assert second.to_position(0, 0) is None


def test_controller_uses_its_injected_mapper():
    mapper = create_mapper()
    engine = GameEngine(Board([[Piece("w", "R")]]))
    controller = Controller(engine, mapper)
    controller.click(50, 50)
    assert engine.get_selected() is None
    controller.click(160, 40)
    assert engine.get_selected() == Position(0, 0)


def test_engine_snapshot_has_semantic_animation_data_only():
    engine = GameEngine(Board([[Piece("w", "R"), None]]))
    engine.select(Position(0, 0))
    engine.move_request(Position(0, 1))
    engine.tick(50)

    moving_piece = next(
        piece for piece in engine.create_snapshot().pieces
        if piece.state == PieceState.MOVE
    )
    assert moving_piece.position == Position(0, 0)
    assert moving_piece.target == Position(0, 1)
    assert 0.0 < moving_piece.progress < 1.0
    assert not hasattr(moving_piece, "pixel_x")
