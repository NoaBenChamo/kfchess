from board_io.board_parser import BoardParser
from engine.game_engine import GameEngine
from input.controller import Controller
from view.image_view import ImageView
from view.renderer import Renderer
from view.game_runner import GameRunner

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

def main():
    board = BoardParser.parse(INITIAL_BOARD.strip().splitlines())
    engine = GameEngine(board)
    controller = Controller(engine)
    image_view = ImageView()
    renderer = Renderer(image_view)
    GameRunner(engine, controller, renderer).run()

if __name__ == "__main__":
    main()
