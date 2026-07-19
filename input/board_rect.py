class BoardRect:
    """
    Describes a rectangular area of the game board inside the full window.

    The coordinates are expressed in full-window pixel coordinates.

    Attributes:
        x: Top-left x coordinate.
        y: Top-left y coordinate.
        width: Width of the board area in pixels.
        height: Height of the board area in pixels.
        cols: Number of board columns.
        rows: Number of board rows.
    """

    def __init__(self, x, y, width, height, cols, rows):
        self._x = x
        self._y = y
        self._width = width
        self._height = height
        self._cols = cols
        self._rows = rows

        self._cell_width = width // cols
        self._cell_height = height // rows

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def cols(self):
        return self._cols

    @property
    def rows(self):
        return self._rows

    @property
    def cell_width(self):
        return self._cell_width

    @property
    def cell_height(self):
        return self._cell_height

    # Aliases used by tests
    @property
    def cell_w(self):
        return self._cell_width

    @property
    def cell_h(self):
        return self._cell_height

    def contains(self, x, y):
        """
        Returns True if the given window coordinates
        are inside the playable board area.
        """
        return (
            self._x <= x < self._x + self._width
            and self._y <= y < self._y + self._height
        )