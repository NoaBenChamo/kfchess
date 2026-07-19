import os
import cv2
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

    MARGIN = 24

    def _load_board(self):
        path = os.path.join(ASSETS_DIR, "board.png")
        board_img = Img().read(path)
        h, w = board_img.img.shape[:2]
        self._cell_width = w // BOARD_COLS
        self._cell_height = h // BOARD_ROWS
        BoardMapper.init(self._cell_width, self._cell_height)

        m = ImageView.MARGIN
        channels = board_img.img.shape[2]
        canvas = np.zeros((h + m, w + m, channels), dtype=np.uint8)
        canvas[:h, m:m + w] = board_img.img

        self._board = Img()
        self._board.img = canvas
        self._draw_labels()
        self._board_clean = self._board.img.copy()

    def _draw_labels(self):
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.4
        color = (255, 255, 255, 255)
        thickness = 1
        m = ImageView.MARGIN
        h, w = self._board.img.shape[:2]

        for col in range(BOARD_COLS):
            letter = chr(ord('A') + col)
            x = m + col * self._cell_width + self._cell_width // 2 - 5
            y = h - 6
            cv2.putText(self._board.img, letter, (x, y), font, font_scale, color, thickness, cv2.LINE_AA)

        for row in range(BOARD_ROWS):
            number = str(BOARD_ROWS - row)
            x = 4
            y = row * self._cell_height + self._cell_height // 2 + 5
            cv2.putText(self._board.img, number, (x, y), font, font_scale, color, thickness, cv2.LINE_AA)

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
        frame.draw_on(self._board, x + ImageView.MARGIN, y)

    def draw_selection(self, x, y):
        overlay = np.zeros((self._cell_height, self._cell_width, 4), dtype=np.uint8)
        overlay[:, :] = (0, 255, 255, 80)
        sel = Img()
        sel.img = overlay
        sel.draw_on(self._board, x + ImageView.MARGIN, y)

    def draw_cooldown(self, x, y, progress):
        bar_h = max(4, self._cell_height // 10)
        bar_w = self._cell_width - 8
        filled_w = int(bar_w * progress)

        bar = np.zeros((bar_h, bar_w, 4), dtype=np.uint8)
        bar[:, :] = (40, 40, 40, 180)
        if filled_w > 0:
            r = int(255 * (1.0 - progress))
            g = int(200 * progress + 55)
            bar[:, :filled_w] = (0, g, r, 220)

        overlay = Img()
        overlay.img = bar
        overlay.draw_on(self._board, x + ImageView.MARGIN + 4, y + self._cell_height - bar_h - 2)

    def draw_game_over(self):
        h, w = self._board.img.shape[:2]
        self._board.put_text("GAME OVER", w // 4, h // 2, 2.0,
                             color=(0, 0, 255, 255), thickness=4)

    def present(self):
        self._board.show()
