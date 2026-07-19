class BoardRect:
    """
    Describes the playable board area inside the full game window.

    All coordinates are expressed in full-window pixels.
    """

    def __init__(self, x, y, width, height, cols, rows):
        if cols <= 0 or rows <= 0:
            raise ValueError("Board rows and columns must be positive")

        if width <= 0 or height <= 0:
            raise ValueError("Board width and height must be positive")

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

    @property
    def cell_w(self):
        """Backward-compatible alias."""
        return self._cell_width

    @property
    def cell_h(self):
        """Backward-compatible alias."""
        return self._cell_height

    @property
    def right(self):
        return self._x + self._width

    @property
    def bottom(self):
        return self._y + self._height

    def contains(self, x, y):
        return (
            self._x <= x < self.right
            and self._y <= y < self.bottom
        )