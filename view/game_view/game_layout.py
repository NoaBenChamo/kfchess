from input.board_rect import BoardRect

BOARD_COLS = 8
BOARD_ROWS = 8


class GameLayout:
    """
    Calculates the pixel geometry for every screen region.

    Layout:
    ┌────────────────────────────────────────────┐
    │                  HEADER                    │
    ├──────────────┬──────────────┬──────────────┤
    │ LEFT PLAYER  │    BOARD     │ RIGHT PLAYER │
    └──────────────┴──────────────┴──────────────┘

    board_rect is the single source of truth for the board's position and
    cell size.  BoardMapper and BoardView both use this object so that
    rendering and mouse input are always in sync.
    """

    HEADER_HEIGHT = 40
    PLAYER_WIDTH  = 160

    def __init__(self, board_w, board_h):
        bx = self.PLAYER_WIDTH
        by = self.HEADER_HEIGHT

        self.board_rect  = BoardRect(bx, by, board_w, board_h, BOARD_COLS, BOARD_ROWS)

        self.total_w = self.PLAYER_WIDTH * 2 + board_w
        self.total_h = self.HEADER_HEIGHT + board_h

        self.header_rect = (0, 0, self.total_w, self.HEADER_HEIGHT)
        self.left_rect   = (0,        by, self.PLAYER_WIDTH, board_h)
        self.right_rect  = (bx + board_w, by, self.PLAYER_WIDTH, board_h)

    def board_origin(self):
        return self.board_rect.x, self.board_rect.y
