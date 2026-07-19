from model.position import Position


class BoardMapper:

    def __init__(self, board_rect):
        self._board_rect = board_rect

    def to_position(self, x, y):
        """
        Converts window pixel coordinates
        to a board Position.

        Returns None when the coordinates
        are outside the playable board.
        """

        if not self._board_rect.contains(x, y):
            return None

        local_x = x - self._board_rect.x
        local_y = y - self._board_rect.y

        col = local_x // self._board_rect.cell_width
        row = local_y // self._board_rect.cell_height

        return Position(
            row,
            col,
        )

    def to_pixels(self, position):
        """
        Converts a board Position to the top-left
        global window pixel coordinates of the cell.
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