from model.position import Position
from input.board_rect import BoardRect

BOARD_COLS = 8
BOARD_ROWS = 8


class BoardMapper:
    """
    Converts between canvas pixel coordinates and board Position objects.

    All conversions are driven by a single BoardRect that is set once at
    startup (or whenever the layout changes).  No offsets are hardcoded
    anywhere else.
    """

    _rect: BoardRect = BoardRect(0, 0, 800, 800, BOARD_COLS, BOARD_ROWS)

    @classmethod
    def init(cls, rect: BoardRect):
        cls._rect = rect

    # ------------------------------------------------------------------ #
    # Canvas → board                                                        #
    # ------------------------------------------------------------------ #

    @classmethod
    def to_position(cls, canvas_x, canvas_y):
        """
        Convert canvas pixel coordinates to a board Position.
        Returns None if the point is outside the board area.
        """
        if not cls._rect.contains(canvas_x, canvas_y):
            return None

        local_x = canvas_x - cls._rect.x
        local_y = canvas_y - cls._rect.y

        return Position(
            local_y // cls._rect.cell_h,
            local_x // cls._rect.cell_w,
        )

    # ------------------------------------------------------------------ #
    # Board → canvas                                                        #
    # ------------------------------------------------------------------ #

    @classmethod
    def to_pixels(cls, position):
        """
        Convert a board Position to canvas pixel coordinates (top-left of cell).
        """
        return (
            cls._rect.x + position.col * cls._rect.cell_w,
            cls._rect.y + position.row * cls._rect.cell_h,
        )

    # ------------------------------------------------------------------ #
    # Convenience accessors used by BoardView                              #
    # ------------------------------------------------------------------ #

    @classmethod
    def cell_width(cls):
        return cls._rect.cell_w

    @classmethod
    def cell_height(cls):
        return cls._rect.cell_h

    @classmethod
    def get_rect(cls):
        return cls._rect
