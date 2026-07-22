import os

EMPTY = "."

VALID_COLORS = {
    "w",
    "b"
}

VALID_PIECES = {
    "K",
    "Q",
    "R",
    "B",
    "N",
    "P"
}

PIECE_SPEED = {
    "K": 100,
    "Q": 100,
    "R": 100,
    "B": 100,
    "N": 100,
    "P": 100,
}

PAWN_START_ROW = {
    "w": 6,
    "b": 1
}

PAWN_PROMOTION_ROW = {
    "w": 0,
    "b": 7
}

JUMP_DURATION = 1000
SHORT_REST_DURATION = 500
LONG_REST_DURATION = 1000

# ------------------------------------------------------------------ #
# Board geometry
# ------------------------------------------------------------------ #

BOARD_COLS = 8
BOARD_ROWS = 8

# ------------------------------------------------------------------ #
# View / UI
# ------------------------------------------------------------------ #

ASSETS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "assets"
)

LABEL_MARGIN     = 24
FRAME_DURATION_MS = 150

HEADER_HEIGHT = 60
FOOTER_HEIGHT = 40
PLAYER_WIDTH  = 300

EXIT_BUTTON_WIDTH = 110
EXIT_BUTTON_HEIGHT = 36
EXIT_BUTTON_MARGIN = 12
EXIT_BUTTON_BG = (55, 55, 140)
EXIT_BUTTON_BG_HOVER = (70, 70, 170)
EXIT_BUTTON_TEXT = (240, 240, 240)

HEADER_BG_COLOR = (30, 30, 30, 255)
FOOTER_BG_COLOR = (30, 30, 30, 255)

PLAYER_BG_COLOR       = (20, 20, 20, 255)
PLAYER_TITLE_COLOR    = (200, 200, 200, 255)
PLAYER_MOVE_COLOR     = (160, 160, 160, 255)
PLAYER_DIVIDER_COLOR  = (60, 60, 60, 255)
PLAYER_PADDING        = 12
PLAYER_TITLE_FONT_SCALE = 0.55
PLAYER_MOVE_FONT_SCALE  = 0.45
PLAYER_SCORE_FONT_SCALE = 0.50
PLAYER_LINE_HEIGHT    = 20
PLAYER_SCORE_LINE_HEIGHT = 18

PLAYER_SCORE_COLOR    = (220, 220, 100, 255)

PLAYER_TABLE_BORDER_COLOR = (90, 90, 90, 255)
PLAYER_TABLE_HEADER_BG    = (35, 35, 35, 255)
PLAYER_TABLE_HEADER_COLOR = (180, 180, 180, 255)
PLAYER_TABLE_TIME_COLOR   = (150, 170, 190, 255)
PLAYER_TABLE_HEADER_HEIGHT = 22
PLAYER_TABLE_ROW_HEIGHT    = 20

WINDOW_NAME = "KFChess"
TICK_MS     = 16