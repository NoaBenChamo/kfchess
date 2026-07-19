import os
import time
import cv2
import numpy as np
from img import Img
from config.constants import VALID_COLORS, VALID_PIECES
from view.piece_state import PieceState
from input.board_mapper import BoardMapper

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "assets")
BOARD_COLS = 8
BOARD_ROWS = 8
LABEL_MARGIN = 24
FRAME_DURATION_MS = 150


class BoardView:
    """
    Renders the chess board onto its own canvas surface.

    The canvas is sized to (board_w + LABEL_MARGIN) × (board_h + LABEL_MARGIN)
    so that coordinate labels fit outside the playable area.

    All sprite/selection/cooldown draw calls use BoardMapper.to_pixels(),
    which already accounts for the board's position in the full game canvas.
    BoardView subtracts the board origin so that drawing lands correctly on
    its local canvas.
    """

    def __init__(self):
        self._canvas = None
        self._canvas_clean = None
        self._images = {}
        self._board_img_w = 0
        self._board_img_h = 0
        self._load_board()
        self._load_pieces()

    # ------------------------------------------------------------------ #
    # Public geometry (canvas surface size, not the playable board size)   #
    # ------------------------------------------------------------------ #

    @property
    def width(self):
        return self._canvas.img.shape[1]

    @property
    def height(self):
        return self._canvas.img.shape[0]

    # ------------------------------------------------------------------ #
    # Initialisation                                                        #
    # ------------------------------------------------------------------ #

    def _load_board(self):
        path = os.path.join(ASSETS_DIR, "board.png")
        board_img = Img().read(path)
        h, w = board_img.img.shape[:2]
        self._board_img_w = w
        self._board_img_h = h

        channels = board_img.img.shape[2]
        canvas_w = w + LABEL_MARGIN
        canvas_h = h + LABEL_MARGIN
        canvas = np.zeros((canvas_h, canvas_w, channels), dtype=np.uint8)
        # Board image sits at (LABEL_MARGIN, 0): left margin for numbers, bottom for letters
        canvas[:h, LABEL_MARGIN:LABEL_MARGIN + w] = board_img.img

        self._canvas = Img()
        self._canvas.img = canvas
        self._draw_labels(w, h)
        self._canvas_clean = self._canvas.img.copy()

    def _draw_labels(self, board_w, board_h):
        cell_w = board_w // BOARD_COLS
        cell_h = board_h // BOARD_ROWS
        font       = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.4
        color      = (255, 255, 255, 255)
        thickness  = 1
        canvas_h   = self._canvas.img.shape[0]

        for col in range(BOARD_COLS):
            letter = chr(ord('A') + col)
            x = LABEL_MARGIN + col * cell_w + cell_w // 2 - 5
            y = canvas_h - 6
            cv2.putText(self._canvas.img, letter, (x, y),
                        font, font_scale, color, thickness, cv2.LINE_AA)

        for row in range(BOARD_ROWS):
            number = str(BOARD_ROWS - row)
            x = 4
            y = row * cell_h + cell_h // 2 + 5
            cv2.putText(self._canvas.img, number, (x, y),
                        font, font_scale, color, thickness, cv2.LINE_AA)

    def _load_pieces(self):
        for color in VALID_COLORS:
            for kind in VALID_PIECES:
                self._load_piece(color + kind)

    def _load_piece(self, piece_key):
        rect = BoardMapper.get_rect()
        self._images[piece_key] = {}
        for state in PieceState:
            sprites_dir = os.path.join(
                ASSETS_DIR, "pieces", piece_key, "states", state.value, "sprites"
            )
            frames = []
            if os.path.isdir(sprites_dir):
                for f in sorted(os.listdir(sprites_dir)):
                    if f.endswith(".png"):
                        frames.append(
                            Img().read(
                                os.path.join(sprites_dir, f),
                                size=(rect.cell_w, rect.cell_h)
                            )
                        )
            self._images[piece_key][state] = frames

    # ------------------------------------------------------------------ #
    # Frame lifecycle                                                       #
    # ------------------------------------------------------------------ #

    def clear(self):
        self._canvas.img = self._canvas_clean.copy()

    def render(self, snapshot):
        self.clear()
        self._draw_pieces(snapshot)
        self._draw_selection(snapshot)
        if snapshot.game_over:
            self._draw_game_over()

    def get_canvas(self):
        return self._canvas

    # ------------------------------------------------------------------ #
    # Drawing primitives                                                    #
    # ------------------------------------------------------------------ #

    def _to_local(self, canvas_x, canvas_y):
        """Convert canvas coordinates to BoardView-local coordinates."""
        rect = BoardMapper.get_rect()
        return canvas_x - rect.x + LABEL_MARGIN, canvas_y - rect.y

    def _draw_pieces(self, snapshot):
        current_ms = int(time.time() * 1000)
        frame = current_ms // FRAME_DURATION_MS
        for piece in snapshot.pieces:
            if piece.pixel_x is not None:
                cx, cy = piece.pixel_x, piece.pixel_y
            else:
                cx, cy = BoardMapper.to_pixels(piece.position)
            lx, ly = self._to_local(cx, cy)
            piece_key = piece.color + piece.piece_type
            self._draw_piece(piece_key, piece.state, frame, lx, ly)
            if piece.rest_progress is not None:
                cx2, cy2 = BoardMapper.to_pixels(piece.position)
                lx2, ly2 = self._to_local(cx2, cy2)
                self._draw_cooldown(lx2, ly2, piece.rest_progress)

    def _draw_selection(self, snapshot):
        if snapshot.selected_cell is None:
            return
        rect = BoardMapper.get_rect()
        cx, cy = BoardMapper.to_pixels(snapshot.selected_cell)
        lx, ly = self._to_local(cx, cy)
        overlay = np.zeros((rect.cell_h, rect.cell_w, 4), dtype=np.uint8)
        overlay[:, :] = (0, 255, 255, 80)
        sel = Img()
        sel.img = overlay
        sel.draw_on(self._canvas, lx, ly)

    def _draw_piece(self, piece_key, state, frame_index, lx, ly):
        frames = self._images.get(piece_key, {}).get(state, [])
        if not frames:
            return
        frames[frame_index % len(frames)].draw_on(self._canvas, lx, ly)

    def _draw_cooldown(self, lx, ly, progress):
        rect  = BoardMapper.get_rect()
        bar_h = max(4, rect.cell_h // 10)
        bar_w = rect.cell_w - 8
        filled_w = int(bar_w * progress)

        bar = np.zeros((bar_h, bar_w, 4), dtype=np.uint8)
        bar[:, :] = (40, 40, 40, 180)
        if filled_w > 0:
            r = int(255 * (1.0 - progress))
            g = int(200 * progress + 55)
            bar[:, :filled_w] = (0, g, r, 220)

        overlay = Img()
        overlay.img = bar
        overlay.draw_on(self._canvas, lx + 4, ly + rect.cell_h - bar_h - 2)

    def _draw_game_over(self):
        h, w = self._canvas.img.shape[:2]
        self._canvas.put_text("GAME OVER", w // 4, h // 2, 2.0,
                              color=(0, 0, 255, 255), thickness=4)
