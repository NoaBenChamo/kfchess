from input.board_rect import BoardRect
from input.screen_rect import ScreenRect
from config.constants import (
    BOARD_COLS,
    BOARD_ROWS,
    HEADER_HEIGHT,
    FOOTER_HEIGHT,
    PLAYER_WIDTH,
    LABEL_MARGIN,
)


class GameLayout:
    """
    Calculates and exposes all screen regions.

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
        self._validate_window_size(window_width, window_height)

        self._total_width = window_width
        self._total_height = window_height

        self._create_layout()

    def _create_layout(self):
        board_canvas_x = PLAYER_WIDTH
        board_canvas_y = HEADER_HEIGHT

        board_canvas_width = (
            self._total_width - 2 * PLAYER_WIDTH
        )

        board_canvas_height = (
            self._total_height
            - HEADER_HEIGHT
            - FOOTER_HEIGHT
        )

        self._board_canvas_rect = ScreenRect(
            x=board_canvas_x,
            y=board_canvas_y,
            width=board_canvas_width,
            height=board_canvas_height,
        )

        self._header_rect = ScreenRect(
            x=0,
            y=0,
            width=self._total_width,
            height=HEADER_HEIGHT,
        )

        self._footer_rect = ScreenRect(
            x=0,
            y=self._total_height - FOOTER_HEIGHT,
            width=self._total_width,
            height=FOOTER_HEIGHT,
        )

        self._left_player_rect = ScreenRect(
            x=0,
            y=HEADER_HEIGHT,
            width=PLAYER_WIDTH,
            height=board_canvas_height,
        )

        self._right_player_rect = ScreenRect(
            x=board_canvas_x + board_canvas_width,
            y=HEADER_HEIGHT,
            width=PLAYER_WIDTH,
            height=board_canvas_height,
        )

        self._board_rect = self._create_board_rect(
            board_canvas_x,
            board_canvas_y,
            board_canvas_width,
            board_canvas_height,
        )

    def _create_board_rect(
        self,
        canvas_x,
        canvas_y,
        canvas_width,
        canvas_height,
    ):
        available_width = canvas_width - LABEL_MARGIN
        available_height = canvas_height - LABEL_MARGIN

        board_width = (
            available_width // BOARD_COLS
        ) * BOARD_COLS

        board_height = (
            available_height // BOARD_ROWS
        ) * BOARD_ROWS

        return BoardRect(
            x=canvas_x + LABEL_MARGIN,
            y=canvas_y,
            width=board_width,
            height=board_height,
            cols=BOARD_COLS,
            rows=BOARD_ROWS,
        )

    def _validate_window_size(self, width, height):
        minimum_width = (
            2 * PLAYER_WIDTH
            + LABEL_MARGIN
            + BOARD_COLS
        )

        minimum_height = (
            HEADER_HEIGHT
            + FOOTER_HEIGHT
            + LABEL_MARGIN
            + BOARD_ROWS
        )

        if width < minimum_width:
            raise ValueError(
                f"Window width must be at least {minimum_width}"
            )

        if height < minimum_height:
            raise ValueError(
                f"Window height must be at least {minimum_height}"
            )

    @property
    def board_rect(self):
        """Playable board area used by BoardMapper and BoardView."""
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