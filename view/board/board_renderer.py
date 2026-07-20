import cv2
import numpy as np

from img import Img
from config.constants import (
    BOARD_COLS,
    BOARD_ROWS,
    LABEL_MARGIN,
)


class BoardRenderer:
    """
    Creates the static board canvas.

    Responsible only for:
        - board background
        - row labels
        - column labels
    """

    def __init__(self, board_rect, assets_manager):
        self._assets_manager = assets_manager

        self._cell_width = board_rect.cell_width
        self._cell_height = board_rect.cell_height
        self._label_margin = LABEL_MARGIN

        self._clean_canvas = None
        self._canvas_width = None
        self._canvas_height = None

    def create_canvas(self, canvas_width, canvas_height):
        """
        Returns a fresh copy of the static board canvas.
        """
        if self._must_rebuild(canvas_width, canvas_height):
            self._build_clean_canvas(canvas_width, canvas_height)

        canvas = Img()
        canvas.img = self._clean_canvas.copy()
        return canvas

    def _must_rebuild(self, canvas_width, canvas_height):
        return (
            self._clean_canvas is None
            or self._canvas_width != canvas_width
            or self._canvas_height != canvas_height
        )

    def _build_clean_canvas(self, canvas_width, canvas_height):
        board_image = self._assets_manager.get_board().img

        if board_image is None:
            raise ValueError("Board image was not loaded")

        channels = self._get_channel_count(board_image)

        canvas = np.zeros(
            (canvas_height, canvas_width, channels),
            dtype=np.uint8,
        )

        board_height, board_width = board_image.shape[:2]

        board_x = self._label_margin
        board_y = 0

        self._validate_board_fits(
            canvas_width,
            canvas_height,
            board_width,
            board_height,
            board_x,
            board_y,
        )

        canvas[
            board_y:board_y + board_height,
            board_x:board_x + board_width,
        ] = board_image

        img = Img()
        img.img = canvas

        self._canvas_width = canvas_width
        self._canvas_height = canvas_height

        self._draw_labels(img)

        self._clean_canvas = img.img.copy()

    def _draw_labels(self, canvas):
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = max(0.3, self._cell_height / 200.0)
        color = (255, 255, 255, 255)
        thickness = 1

        self._draw_column_labels(
            canvas,
            font,
            font_scale,
            color,
            thickness,
        )

        self._draw_row_labels(
            canvas,
            font,
            font_scale,
            color,
            thickness,
        )

    def _draw_column_labels(
        self,
        canvas,
        font,
        font_scale,
        color,
        thickness,
    ):
        for col in range(BOARD_COLS):
            label = chr(ord("A") + col)

            x = (
                self._label_margin
                + col * self._cell_width
                + self._cell_width // 2
                - 5
            )

            y = self._canvas_height - 6

            cv2.putText(
                canvas.img,
                label,
                (x, y),
                font,
                font_scale,
                color,
                thickness,
                cv2.LINE_AA,
            )

    def _draw_row_labels(
        self,
        canvas,
        font,
        font_scale,
        color,
        thickness,
    ):
        for row in range(BOARD_ROWS):
            label = str(BOARD_ROWS - row)

            x = 4
            y = (
                row * self._cell_height
                + self._cell_height // 2
                + 5
            )

            cv2.putText(
                canvas.img,
                label,
                (x, y),
                font,
                font_scale,
                color,
                thickness,
                cv2.LINE_AA,
            )

    def _validate_board_fits(
        self,
        canvas_width,
        canvas_height,
        board_width,
        board_height,
        board_x,
        board_y,
    ):
        if board_x + board_width > canvas_width:
            raise ValueError(
                "Board image is wider than the board canvas"
            )

        if board_y + board_height > canvas_height:
            raise ValueError(
                "Board image is taller than the board canvas"
            )

    @staticmethod
    def _get_channel_count(image):
        if len(image.shape) == 2:
            return 1

        return image.shape[2]