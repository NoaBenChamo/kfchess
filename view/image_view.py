import os
import numpy as np
from img import Img
from config.constants import VALID_COLORS, VALID_PIECES
from view.piece_state import PieceState
from input.board_mapper import BoardMapper

#TODO 
#move this to constants
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")
BOARD_COLS = 8
BOARD_ROWS = 8

#show the state on the screen
class ImageView:

    def __init__(self):
        self._board = None
        self._images = {}
        self._cell_width = 100
        self._cell_height = 100
        self._load_board()
        self._load_pieces()

    def _load_board(self):
        path = os.path.join(ASSETS_DIR, "board.png")
        self._board = Img().read(path)
        h, w = self._board.img.shape[:2]
        self._cell_width = w // BOARD_COLS
        self._cell_height = h // BOARD_ROWS
        BoardMapper.init(self._cell_width, self._cell_height)
        self._board_clean = self._board.img.copy()

    def _load_pieces(self):
        for color in VALID_COLORS:
            for kind in VALID_PIECES:
                self._load_piece(color + kind)

    def _load_piece(self, piece_key):
        self._images[piece_key] = {}
        for state in PieceState:
            sprites_dir = os.path.join(
                ASSETS_DIR, "pieces", piece_key, "states", state.value, "sprites"
            )
            frames = []
            if os.path.isdir(sprites_dir):
                files = sorted(os.listdir(sprites_dir))
                for f in files:
                    if f.endswith(".png"):
                        frames.append(
                            Img().read(
                                os.path.join(sprites_dir, f),
                                size=(self._cell_width, self._cell_height)
                            )
                        )
            self._images[piece_key][state] = frames

    def clear(self):
        self._board.img = self._board_clean.copy()

    def draw_piece(self, piece_key, state, frame_index, x, y):
        frames = self._images.get(piece_key, {}).get(state, [])
        if not frames:
            return
        frame = frames[frame_index % len(frames)]
        frame.draw_on(self._board, x, y)

    def draw_selection(self, x, y):
        overlay = np.zeros((self._cell_height, self._cell_width, 4), dtype=np.uint8)
        overlay[:, :] = (0, 255, 255, 80)
        sel = Img()
        sel.img = overlay
        sel.draw_on(self._board, x, y)

    def draw_cooldown(self, x, y, progress):
        """Draw an hourglass cooldown bar at the bottom of the cell.
        progress: 0.0 = just started resting, 1.0 = rest complete.
        """
        bar_h = max(4, self._cell_height // 10)
        bar_w = self._cell_width - 8
        filled_w = int(bar_w * progress)

        bar = np.zeros((bar_h, bar_w, 4), dtype=np.uint8)
        # background: dark gray
        bar[:, :] = (40, 40, 40, 180)
        # fill: yellow → green as progress increases
        if filled_w > 0:
            r = int(255 * (1.0 - progress))
            g = int(200 * progress + 55)
            bar[:, :filled_w] = (0, g, r, 220)

        overlay = Img()
        overlay.img = bar
        bx = x + 4
        by = y + self._cell_height - bar_h - 2
        overlay.draw_on(self._board, bx, by)

    def draw_game_over(self):
        h, w = self._board.img.shape[:2]
        self._board.put_text("GAME OVER", w // 4, h // 2, 2.0,
                             color=(0, 0, 255, 255), thickness=4)

    def present(self):
        self._board.show()
