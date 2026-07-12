from input.controller import Controller
from model.board import Board


class FakeGameEngine:

    def __init__(self, board):

        self.board = board
        self.moves = []


    def get_board(self):

        return self.board


    def move_request(self, source, target):

        self.moves.append(
            (source, target)
        )



def create_board():

    return Board([
        ["WR", ".", "."],
        [".", ".", "."],
        [".", ".", "BK"]
    ])



def test_first_click_selects_piece():

    board = create_board()

    engine = FakeGameEngine(board)

    controller = Controller(engine)


    controller.click(
        50,
        50
    )


    assert controller._selected == (0, 0)



def test_second_click_requests_move():

    board = create_board()

    engine = FakeGameEngine(board)

    controller = Controller(engine)


    controller.click(
        50,
        50
    )


    controller.click(
        150,
        50
    )


    assert engine.moves == [
        (
            (0, 0),
            (0, 1)
        )
    ]



def test_click_outside_board_is_ignored():

    board = create_board()

    engine = FakeGameEngine(board)

    controller = Controller(engine)


    controller.click(
        500,
        500
    )


    assert controller._selected is None