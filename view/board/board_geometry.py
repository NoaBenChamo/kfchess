from config.constants import LABEL_MARGIN


class BoardGeometry:
    """
    Converts board positions into local board-canvas pixel coordinates.

    This class contains view geometry only.
    It does not read input and does not change game state.
    """

    def __init__(self, board_rect):
        self._cell_width = board_rect.cell_width
        self._cell_height = board_rect.cell_height
        self._label_margin = LABEL_MARGIN

    def position_to_local(self, position):
        """
        Converts a board Position into the top-left pixel coordinates
        of its cell inside the local board canvas.
        """
        return self.cell_to_local(
            row=position.row,
            col=position.col,
        )

    def cell_to_local(self, row, col):
        """
        Converts board row and column values into local canvas pixels.
        """
        x = self._label_margin + col * self._cell_width
        y = row * self._cell_height

        return x, y

    def cell_center_to_local(self, position):
        """
        Returns the center pixel of a board cell
        inside the local board canvas.
        """
        x, y = self.position_to_local(position)

        return (
            x + self._cell_width // 2,
            y + self._cell_height // 2,
        )

    @property
    def cell_width(self):
        return self._cell_width

    @property
    def cell_height(self):
        return self._cell_height

    @property
    def label_margin(self):
        return self._label_margin