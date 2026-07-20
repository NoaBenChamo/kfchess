import numpy as np

from img import Img


class HighlightRenderer:
    """
    Draws the currently selected board cell.
    """

    def __init__(self, board_geometry):
        self._geometry = board_geometry

    def render(self, canvas, selected_cell):
        """
        Draws a translucent highlight over the selected cell.
        """
        if selected_cell is None:
            return

        x, y = self._geometry.position_to_local(selected_cell)

        overlay = np.zeros(
            (
                self._geometry.cell_height,
                self._geometry.cell_width,
                4,
            ),
            dtype=np.uint8,
        )

        overlay[:, :] = (
            0,
            255,
            255,
            80,
        )

        image = Img()
        image.img = overlay

        image.draw_on(
            canvas,
            x,
            y,
        )
