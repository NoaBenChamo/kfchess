import cv2
import numpy as np


class Renderer:
    """
    Coordinates rendering of the complete game window.

    Rendering order:

        Header
        Left player panel
        Board
        Right player panel
        Footer
    """

    def __init__(
        self,
        layout,
        header_view,
        left_player_view,
        board_view,
        right_player_view,
        footer_view,
    ):
        self._layout = layout

        self._header_view = header_view
        self._left_player_view = left_player_view
        self._board_view = board_view
        self._right_player_view = right_player_view
        self._footer_view = footer_view

    def render(self, snapshot):
        """
        Renders one complete game frame.

        Returns:
            Img containing the whole window.
        """

        self._header_view.render(snapshot)
        self._left_player_view.render(snapshot)
        self._board_view.render(snapshot)
        self._right_player_view.render(snapshot)
        self._footer_view.render(snapshot)

        return self._compose_window()

    def _compose_window(self):
        """
        Combines every rendered region into one window image.
        """

        window = np.zeros(
            (
                self._layout.total_height,
                self._layout.total_width,
                4,
            ),
            dtype=np.uint8,
        )

        self._paste(
            window,
            self._header_view.get_canvas().img,
            self._layout.header_rect,
        )

        self._paste(
            window,
            self._left_player_view.get_canvas().img,
            self._layout.left_player_rect,
        )

        self._paste(
            window,
            self._board_view.get_canvas().img,
            self._layout.board_canvas_rect,
        )

        self._paste(
            window,
            self._right_player_view.get_canvas().img,
            self._layout.right_player_rect,
        )

        self._paste(
            window,
            self._footer_view.get_canvas().img,
            self._layout.footer_rect,
        )

        return window

    @staticmethod
    def _paste(window, image, rect):
        """
        Copies one rendered region into the final window.
        """

        if image is None:
            return

        h, w = image.shape[:2]

        window[
            rect.y:rect.y + h,
            rect.x:rect.x + w,
        ] = image

    @staticmethod
    def show(window, title="Kung-Fu Chess"):
        """
        Displays the rendered window.
        """

        cv2.imshow(title, window)