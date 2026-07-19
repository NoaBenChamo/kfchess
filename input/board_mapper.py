from model.position import Position


class BoardMapper:
    """
    Converts between full-window pixel coordinates
    and logical board positions.
    """

    def __init__(self, board_rect):
        self._board_rect = board_rect

    def to_position(self, x, y):
        """
        Converts full-window pixel coordinates into a board Position.

        Returns:
            Position when the coordinates are inside the playable board.
            None when the coordinates are outside the board.
        """
        if not self._board_rect.contains(x, y):
            return None

        local_x = x - self._board_rect.x
        local_y = y - self._board_rect.y

        col = local_x // self._board_rect.cell_width
        row = local_y // self._board_rect.cell_height

        return Position(
            row=row,
            col=col,
        )

    def to_pixels(self, position):
        """
        Converts a board Position into the top-left full-window
        pixel coordinates of its cell.
        """
        x = (
            self._board_rect.x
            + position.col * self._board_rect.cell_width
        )

        y = (
            self._board_rect.y
            + position.row * self._board_rect.cell_height
        )

        return x, y

    def cell_width(self):
        return self._board_rect.cell_width

    def cell_height(self):
        return self._board_rect.cell_height

    def get_rect(self):
        return self._board_rect