from model.position import Position
from model.piece import Piece
from model.board import Board

from realtime.move import Move



def test_move_finish():

    piece = Piece("W","R")


    move = Move(
        piece,
        Position(0,0),
        Position(0,1),
        0,
        100
    )


    assert not move.is_finished(50)

    assert move.is_finished(100)