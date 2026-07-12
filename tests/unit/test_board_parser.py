from board_io.board_parser import BoardParser
from model.position import Position
from model.piece import Piece


def test_parse_simple_board():

    lines = [
        "Board:",
        "WR .",
        ". BK",
        "Commands:"
    ]

    board = BoardParser.parse(lines)

    white_rook = board.get(Position(0, 0))
    black_king = board.get(Position(1, 1))

    assert isinstance(white_rook, Piece)
    assert white_rook.color == "W"
    assert white_rook.type == "R"

    assert isinstance(black_king, Piece)
    assert black_king.color == "B"
    assert black_king.type == "K"


def test_parse_board_size():

    lines = [
        "Board:",
        "WR . .",
        ". BK .",
        "Commands:"
    ]

    board = BoardParser.parse(lines)

    rows = board.get_rows()

    assert len(rows) == 2
    assert len(rows[0]) == 3


def test_parse_stops_at_commands():

    lines = [
        "Board:",
        "WR .",
        "Commands:",
        "WR WR"
    ]

    board = BoardParser.parse(lines)

    assert len(board.get_rows()) == 1


def test_empty_lines_are_ignored():

    lines = [
        "Board:",
        "",
        "WR .",
        "",
        "Commands:"
    ]

    board = BoardParser.parse(lines)

    assert len(board.get_rows()) == 1