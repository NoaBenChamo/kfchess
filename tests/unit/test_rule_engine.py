from rules.rule_engine import RuleEngine
from model.board import Board


def test_rook_valid_move():
    board = Board([
        ["WR", ".", "."],
        [".", ".", "."],
        [".", ".", "BK"]
    ])

    engine = RuleEngine()

    result = engine.validate_move(
        "WR",
        (0, 0),
        (0, 2),
        board
    )

    assert result is True


def test_rook_blocked_move():

    board = Board([
        ["WR", "WP", "."],
        [".", ".", "."],
        [".", ".", "BK"]
    ])

    engine = RuleEngine()

    result = engine.validate_move(
        "WR",
        (0, 0),
        (0, 2),
        board
    )

    assert result is False


def test_invalid_piece_type():

    board = Board([
        ["WK", ".", "."],
        [".", ".", "."],
        [".", ".", "BK"]
    ])

    engine = RuleEngine()

    result = engine.validate_move(
        "WK",
        (0, 0),
        (0, 2),
        board
    )

    assert result is False