from realtime.real_time_arbiter import RealTimeArbiter
from realtime.move import Move
from realtime.jump import Jump
from model.board import Board


def create_board():

    return Board([
        ["WR", ".", "."],
        [".", ".", "."],
        [".", ".", "BK"]
    ])



def test_move_not_finished_immediately():

    board = create_board()

    arbiter = RealTimeArbiter(board)


    move = Move(
        "WR",
        (0, 0),
        (0, 2),
        0,
        1000
    )


    arbiter.add_move(move)


    # הכלי עדיין במקום המקורי
    assert board.get(0, 0) == "WR"
    assert board.get(0, 2) == "."



def test_move_finishes_after_wait():

    board = create_board()

    arbiter = RealTimeArbiter(board)


    move = Move(
        "WR",
        (0, 0),
        (0, 2),
        0,
        1000
    )


    arbiter.add_move(move)


    arbiter.wait(1000)


    assert board.get(0, 0) == "."
    assert board.get(0, 2) == "WR"



def test_move_does_not_finish_before_time():

    board = create_board()

    arbiter = RealTimeArbiter(board)


    move = Move(
        "WR",
        (0, 0),
        (0, 2),
        0,
        1000
    )


    arbiter.add_move(move)


    arbiter.wait(500)


    assert board.get(0, 0) == "WR"
    assert board.get(0, 2) == "."



def test_jump_finishes_after_time():

    board = create_board()

    arbiter = RealTimeArbiter(board)


    jump = Jump(
        (0, 0),
        "WR",
        0,
        1000
    )


    arbiter.add_jump(jump)


    assert arbiter.is_jumping((0, 0))


    arbiter.wait(1000)


    assert not arbiter.is_jumping((0, 0))