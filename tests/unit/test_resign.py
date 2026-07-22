from model.board import Board
from model.piece import Piece

from engine.game_engine import GameEngine


def test_resign_ends_game_and_sets_opponent_winner():
    engine = GameEngine(Board([[Piece("w", "K"), Piece("b", "K")]]))

    assert engine.resign("w") is True
    assert engine.is_game_over()
    assert engine.get_winner() == "b"


def test_resign_is_idempotent():
    engine = GameEngine(Board([[Piece("w", "K")]]))
    assert engine.resign("b") is True
    assert engine.resign("b") is False
    assert engine.get_winner() == "w"
