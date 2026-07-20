import numpy as np


class WindowComposer:
    """
    Creates the shared canvas used by all screen views.
    """

    CHANNELS = 4

    def __init__(self, width, height):
        if width <= 0 or height <= 0:
            raise ValueError("Window dimensions must be positive")

        self._width = width
        self._height = height

    def create_canvas(self):
        """
        Creates a clean transparent BGRA canvas.
        """
        return np.zeros(
            (
                self._height,
                self._width,
                self.CHANNELS,
            ),
            dtype=np.uint8,
        )