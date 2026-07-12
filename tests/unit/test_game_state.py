from model.board import Board
from model.game_state import GameState


def test_snapshot_contains_current_state():

    board = Board([
        ["WR", "."],
        [".", "BK"]
    ])


    state = GameState(board)


    state.set_selected(
        (0, 0)
    )


    snapshot = state.snapshot()


    assert snapshot.get_board() == board

    assert snapshot.get_selected() == (
        0,
        0
    )

    assert snapshot.is_game_over() is False



def test_game_over_saved_in_snapshot():

    board = Board([
        ["WK", "."],
        [".", "BK"]
    ])


    state = GameState(board)


    state.set_game_over()


    snapshot = state.snapshot()


    assert snapshot.is_game_over() is True