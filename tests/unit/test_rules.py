from model.position import Position
from model.piece import Piece
from model.board import Board

from rules.piece_rules.rook_rule import RookRule



def test_rook_move():

    board = Board(
        [
            [
                Piece("W","R"),
                None,
                None
            ]
        ]
    )


    rule = RookRule()


    result = rule.can_move(
        Piece("W","R"),
        Position(0,0),
        Position(0,2),
        board
    )


    assert result