from board_io.board_parser import BoardParser
from engine.game_engine import GameEngine
from input.controller import Controller
from view.factory import create_ui
from view.game_runner import GameRunner, get_work_area


INITIAL_BOARD = """
Board:
bR bN bB bQ bK bB bN bR
bP bP bP bP bP bP bP bP
.  .  .  .  .  .  .  .
.  .  .  .  .  .  .  .
.  .  .  .  .  .  .  .
.  .  .  .  .  .  .  .
wP wP wP wP wP wP wP wP
wR wN wB wQ wK wB wN wR
"""


def create_game():
    """
    Creates and connects all game components.

    Returns:
        GameRunner: Fully configured game runner.
    """
    board = BoardParser.parse(
        INITIAL_BOARD.strip().splitlines()
    )

    engine = GameEngine(board)

    window_width, window_height = get_work_area()
    ui = create_ui(window_width, window_height)

    controller = Controller(
        game_engine=engine,
        board_mapper=ui.board_mapper,
    )

    return GameRunner(
        engine=engine,
        controller=controller,
        renderer=ui.renderer,
    )


def main():
    game_runner = create_game()
    game_runner.run()


if __name__ == "__main__":
    main()
