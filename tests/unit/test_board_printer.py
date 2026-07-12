from board_io.board_printer import BoardPrinter

from model.board import Board
from model.piece import Piece


def test_print_empty_board(capsys):

    board = Board([
        [None, None],
        [None, None]
    ])

    BoardPrinter.print(board)

    captured = capsys.readouterr()

    assert captured.out == ". .\n. .\n"



def test_print_board_with_pieces(capsys):

    board = Board([
        [
            Piece("W", "R"),
            None
        ],
        [
            None,
            Piece("B", "K")
        ]
    ])

    BoardPrinter.print(board)

    captured = capsys.readouterr()

    assert captured.out == "WR .\n. BK\n"



def test_print_single_row(capsys):

    board = Board([
        [
            Piece("W", "Q")
        ]
    ])

    BoardPrinter.print(board)

    captured = capsys.readouterr()

    assert captured.out == "WQ\n"