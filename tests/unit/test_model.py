from model.position import Position
from model.piece import Piece
from model.board import Board


def test_piece():

    piece = Piece("W", "K")

    assert piece.color == "W"
    assert piece.type == "K"



def test_position():

    p1 = Position(1, 2)
    p2 = Position(1, 2)

    assert p1 == p2



def test_board():

    piece = Piece("W", "K")

    board = Board([
        [piece, None]
    ])

    pos = Position(0,0)

    assert board.get(pos) == piece
    assert board.is_inside(pos)