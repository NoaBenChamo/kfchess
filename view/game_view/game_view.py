import numpy as np

from img import Img
from input.board_mapper import BoardMapper

from view.game_view.game_layout import GameLayout
from view.game_view.board_view import BoardView
from view.game_view.header_view import HeaderView
from view.game_view.footer_view import FooterView
from view.game_view.player_view import PlayerView
from view.assets_manager import AssetsManager


class GameView:
    """
    Composes the complete game screen from independent visual regions.

    Responsibilities:
        - receive the window size and build the layout from it
        - create the full-screen canvas
        - delegate rendering to HeaderView, PlayerView(×2), BoardView
        - composite all regions into the final image

    Does not contain chess logic, input handling, or movement logic.
    """

    def __init__(self, window_width, window_height):
        self._layout = GameLayout(window_width, window_height)

        self._board_mapper = BoardMapper(self._layout.board_rect)
        assets_manager = AssetsManager(self._layout.board_rect)

        self._board_view = BoardView(
            board_rect=self._layout.board_rect,
            canvas_width=self._layout.board_canvas_rect.width,
            canvas_height=self._layout.board_canvas_rect.height,
            assets_manager=assets_manager,
        )
        self._header_view = HeaderView()
        self._footer_view = FooterView()
        self._left_player_view = PlayerView("White")
        self._right_player_view = PlayerView("Black")

        self._canvas = np.zeros(
            (window_height, window_width, 4),
            dtype=np.uint8,
        )

    # ------------------------------------------------------------------ #
    # Rendering
    # ------------------------------------------------------------------ #

    def render(self, snapshot):
        self._board_view.render(snapshot)
        self._canvas.fill(0)
        self._render_header()
        self._render_footer()
        self._render_players(snapshot)
        self._render_board()

    def _render_header(self):
        self._header_view.render(self._canvas, self._layout.header_rect)

    def _render_footer(self):
        self._footer_view.render(self._canvas, self._layout.footer_rect)

    def _render_players(self, snapshot):
        self._left_player_view.render(
            self._canvas, self._layout.left_player_rect, snapshot.white_moves
        )
        self._right_player_view.render(
            self._canvas, self._layout.right_player_rect, snapshot.black_moves
        )

    def _render_board(self):
        board_canvas = self._board_view.get_canvas().img
        rect = self._layout.board_canvas_rect
        h, w = board_canvas.shape[:2]
        self._canvas[rect.y:rect.y + h, rect.x:rect.x + w] = board_canvas

    # ------------------------------------------------------------------ #
    # Presentation
    # ------------------------------------------------------------------ #

    def present(self):
        display = Img()
        display.img = self._canvas
        display.show()

    @property
    def board_mapper(self):
        """The input mapper that shares this view's board geometry."""
        return self._board_mapper
