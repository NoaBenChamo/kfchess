class BoardRect:
    """
    Immutable description of the board's position and cell size inside
    the full game canvas.

    This is the single source of truth shared by BoardMapper (input) and
    BoardView (rendering).  Any offset — player panels, header, internal
    margin — is captured here once and used everywhere.

    Attributes
    ----------
    x, y        : top-left corner of the board in canvas coordinates
    board_w, board_h : pixel dimensions of the playable board area
    cols, rows  : number of board columns / rows
    cell_w, cell_h  : pixel size of one cell
    """

    def __init__(self, x, y, board_w, board_h, cols, rows):
        self.x = x
        self.y = y
        self.board_w = board_w
        self.board_h = board_h
        self.cols = cols
        self.rows = rows
        self.cell_w = board_w // cols
        self.cell_h = board_h // rows

    def contains(self, canvas_x, canvas_y):
        """Return True if the canvas point is inside the board area."""
        return (
            self.x <= canvas_x < self.x + self.board_w
            and self.y <= canvas_y < self.y + self.board_h
        )
