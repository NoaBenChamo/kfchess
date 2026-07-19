from board_io.board_parser import BoardParser
from engine.game_engine import GameEngine
from input.controller import Controller
from view.game_runner import GameRunner, get_work_area
from view.game_view.game_view import GameView
from view.rendering.renderer import Renderer


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

    work_area_width, work_area_height = get_work_area()

    game_view = GameView(
        work_area_width,
        work_area_height,
    )

    controller = Controller(
        game_engine=engine,
        board_mapper=game_view.board_mapper,
    )

    renderer = Renderer(game_view)

    return GameRunner(
        engine=engine,
        controller=controller,
        renderer=renderer,
    )


def main():
    game_runner = create_game()
    game_runner.run()


if __name__ == "__main__":
    main()