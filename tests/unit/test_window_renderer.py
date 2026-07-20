from board_io.board_parser import BoardParser
from engine.game_engine import GameEngine
from view.factory import create_ui


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


def test_window_renderer_produces_bgra_frame_at_layout_size():
    ui = create_ui(1280, 900)
    board = BoardParser.parse(INITIAL_BOARD.strip().splitlines())
    engine = GameEngine(board)

    snapshot = engine.create_snapshot()
    frame = ui.renderer.render(snapshot, 0)

    assert frame.shape == (900, 1280, 4)
