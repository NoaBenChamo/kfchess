class ScreenRect:
    """
    Describes a rectangular screen area in full-window pixel coordinates.
    """

    def __init__(self, x, y, width, height):
        if width < 0 or height < 0:
            raise ValueError(
                "Screen rectangle width and height cannot be negative"
            )

        self._x = x
        self._y = y
        self._width = width
        self._height = height

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