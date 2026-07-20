from model.board import Board
from model.piece import Piece
from model.position import Position

from engine.game_engine import GameEngine


def test_snapshot_includes_capture_scores():
    board = Board([
        [Piece("w", "R"), Piece("b", "P")],
        [None, None],
    ])

    engine = GameEngine(board)
    engine.select(Position(0, 0))
    engine.move_request(Position(0, 1))

    snapshot = engine.create_snapshot()

    assert snapshot.white_score == 1
    assert snapshot.black_score == 0


def test_snapshot_scores_start_at_zero():
    board = Board([[None]])
    engine = GameEngine(board)

    snapshot = engine.create_snapshot()

    assert snapshot.white_score == 0
    assert snapshot.black_score == 0
