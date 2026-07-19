import numpy as np
from img import Img
from input.board_mapper import BoardMapper
from view.game_view.game_layout import GameLayout
from view.game_view.board_view import BoardView
from view.game_view.header_view import HeaderView
from view.game_view.player_view import PlayerView


class GameView:
    """
    Coordinates the complete screen layout:

    ┌────────────────────────────────────────────┐
    │                  HEADER                    │
    ├──────────────┬──────────────┬──────────────┤
    │ LEFT PLAYER  │    BOARD     │ RIGHT PLAYER │
    └──────────────┴──────────────┴──────────────┘

    Owns the full-screen canvas and delegates rendering to
    HeaderView, PlayerView (×2), and BoardView.
    """

    def __init__(self):
        self._board_view   = BoardView()
        self._header_view  = HeaderView()
        self._left_player  = PlayerView()
        self._right_player = PlayerView()

        # BoardView canvas includes LABEL_MARGIN; the playable board image
        # inside it is (width - LABEL_MARGIN) × (height - LABEL_MARGIN).
        from view.game_view.board_view import LABEL_MARGIN
        board_w = self._board_view.width  - LABEL_MARGIN
        board_h = self._board_view.height - LABEL_MARGIN
        self._layout = GameLayout(board_w, board_h)

        # Single source of truth: BoardMapper uses the layout's BoardRect.
        BoardMapper.init(self._layout.board_rect)

        # The full canvas must fit the BoardView canvas (playable + LABEL_MARGIN)
        board_canvas_w = self._board_view.width
        board_canvas_h = self._board_view.height
        channels = self._board_view.get_canvas().img.shape[2]
        self._canvas = np.zeros(
            (self._layout.HEADER_HEIGHT + board_canvas_h,
             self._layout.PLAYER_WIDTH * 2 + board_canvas_w,
             channels),
            dtype=np.uint8
        )

    # ------------------------------------------------------------------ #
    # Public API used by Renderer                                          #
    # ------------------------------------------------------------------ #

    def render(self, snapshot):
        self._board_view.render(snapshot)
        self._composite()

    def present(self):
        display = Img()
        display.img = self._canvas
        display.show()

    # ------------------------------------------------------------------ #
    # Internal compositing                                                  #
    # ------------------------------------------------------------------ #

    def _composite(self):
        layout = self._layout

        self._header_view.render(self._canvas, layout.header_rect)
        self._left_player.render(self._canvas, layout.left_rect)
        self._right_player.render(self._canvas, layout.right_rect)

        bx, by = layout.board_origin()
        board_img = self._board_view.get_canvas().img
        bh, bw = board_img.shape[:2]
        self._canvas[by:by + bh, bx:bx + bw] = board_img
