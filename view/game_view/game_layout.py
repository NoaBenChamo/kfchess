from input.board_rect import BoardRect
from input.screen_rect import ScreenRect
from config.constants import (
    BOARD_COLS, BOARD_ROWS,
    HEADER_HEIGHT, FOOTER_HEIGHT, PLAYER_WIDTH, LABEL_MARGIN,
)


class GameLayout:
    """
    Single source of truth for the geometry of all screen regions.
    Layout:
        ┌────────────────────────────────────────────┐
        │                  HEADER                    │
        ├──────────────┬──────────────┬──────────────┤
        │ LEFT PLAYER  │    BOARD     │ RIGHT PLAYER │
        ├──────────────┴──────────────┴──────────────┤
        │                  FOOTER                    │
        └────────────────────────────────────────────┘
    """

    def __init__(self, window_width, window_height):
        self._total_width  = window_width
        self._total_height = window_height

        board_canvas_x = PLAYER_WIDTH
        board_canvas_y = HEADER_HEIGHT
        board_canvas_w = window_width  - 2 * PLAYER_WIDTH
        board_canvas_h = window_height - HEADER_HEIGHT - FOOTER_HEIGHT

        raw_board_w = board_canvas_w - LABEL_MARGIN
        raw_board_h = board_canvas_h - LABEL_MARGIN
        board_w = (raw_board_w // BOARD_COLS) * BOARD_COLS
        board_h = (raw_board_h // BOARD_ROWS) * BOARD_ROWS

        board_x = board_canvas_x + LABEL_MARGIN
        board_y = board_canvas_y

        self._board_rect = BoardRect(
            x=board_x,
            y=board_y,
            width=board_w,
            height=board_h,
            cols=BOARD_COLS,
            rows=BOARD_ROWS,
        )

        self._board_canvas_rect = ScreenRect(
            x=board_canvas_x,
            y=board_canvas_y,
            width=board_canvas_w,
            height=board_canvas_h,
        )

        self._footer_rect = ScreenRect(
            x=0,
            y=window_height - FOOTER_HEIGHT,
            width=window_width,
            height=FOOTER_HEIGHT,
        )

        self._header_rect = ScreenRect(
            x=0,
            y=0,
            width=window_width,
            height=HEADER_HEIGHT,
        )

        self._left_player_rect = ScreenRect(
            x=0,
            y=HEADER_HEIGHT,
            width=PLAYER_WIDTH,
            height=board_canvas_h,
        )

        self._right_player_rect = ScreenRect(
            x=PLAYER_WIDTH + board_canvas_w,
            y=HEADER_HEIGHT,
            width=PLAYER_WIDTH,
            height=board_canvas_h,
        )



    @property
    def board_rect(self):
        """Playable board area — used by BoardMapper and BoardView."""
        return self._board_rect

    @property
    def board_canvas_rect(self):
        return self._board_canvas_rect

    @property
    def header_rect(self):
        return self._header_rect

    @property
    def footer_rect(self):
        return self._footer_rect

    @property
    def left_player_rect(self):
        return self._left_player_rect

    @property
    def right_player_rect(self):
        return self._right_player_rect


    @property
    def total_width(self):
        return self._total_width

    @property
    def total_height(self):
        return self._total_height
