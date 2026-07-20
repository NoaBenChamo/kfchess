import numpy as np

from img import Img


class RestOverlayRenderer:
    """
    Draws the cooldown/rest progress bar for pieces.
    """

    def __init__(self, board_geometry):
        self._geometry = board_geometry

    def render(self, canvas, pieces):
        """
        Draws cooldown bars for all pieces that are currently resting.
        """
        for piece in pieces:
            if piece.rest_progress is None:
                continue

            x, y = self._geometry.position_to_local(
                piece.position
            )

            self._draw_progress_bar(
                canvas=canvas,
                x=x,
                y=y,
                progress=piece.rest_progress,
            )

    def _draw_progress_bar(
        self,
        canvas,
        x,
        y,
        progress,
    ):
        progress = self._clamp_progress(progress)
        cell_width = self._geometry.cell_width
        cell_height = self._geometry.cell_height

        bar_height = max(
            4,
            cell_height // 10,
        )

        bar_width = max(
            1,
            cell_width - 8,
        )

        filled_width = int(bar_width * progress)

        bar = np.zeros(
            (bar_height, bar_width, 4),
            dtype=np.uint8,
        )

        bar[:, :] = (
            40,
            40,
            40,
            180,
        )

        if filled_width > 0:
            red = int(255 * (1.0 - progress))
            green = int(55 + 200 * progress)

            bar[:, :filled_width] = (
                0,
                green,
                red,
                220,
            )

        image = Img()
        image.img = bar

        image.draw_on(
            canvas,
            x + 4,
            y + cell_height - bar_height - 2,
        )

    @staticmethod
    def _clamp_progress(progress):
        if progress is None:
            return 0.0

        return max(
            0.0,
            min(1.0, progress),
        )
