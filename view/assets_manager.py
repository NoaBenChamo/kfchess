import os

from img import Img
from config.constants import (
    VALID_COLORS,
    VALID_PIECES,
    ASSETS_DIR,
)
from model.piece_state import PieceState


class AssetsManager:

    def __init__(self, board_rect):
        self._board_rect = board_rect
        self._cell_width = board_rect.cell_width
        self._cell_height = board_rect.cell_height

        self._board = None
        self._images = {}

        self._load_board()
        self._load_pieces()

    def _load_board(self):
        board_path = os.path.join(
            ASSETS_DIR,
            "board.png",
        )

        self._board = Img().read(
            board_path,
            size=(self._board_rect.width, self._board_rect.height),
        )

    def _load_pieces(self):
        for color in VALID_COLORS:
            for piece_type in VALID_PIECES:
                piece_key = color + piece_type
                self._load_piece_sprites(piece_key)

    def _load_piece_sprites(self, piece_key):
        self._images[piece_key] = {}

        for state in PieceState:
            self._images[piece_key][state] = (
                self._load_state_frames(
                    piece_key,
                    state,
                )
            )

    def _load_state_frames(self, piece_key, state):
        sprites_dir = os.path.join(
            ASSETS_DIR,
            "pieces",
            piece_key,
            "states",
            state.value,
            "sprites",
        )

        if not os.path.isdir(sprites_dir):
            return []

        frames = []

        for filename in sorted(os.listdir(sprites_dir)):
            if not filename.endswith(".png"):
                continue

            frame_path = os.path.join(
                sprites_dir,
                filename,
            )

            frame = Img().read(
                frame_path,
                size=(
                    self._cell_width,
                    self._cell_height,
                ),
            )

            frames.append(frame)

        return frames

    def get_board(self):
        return self._board

    def get_piece_frames(self, piece_key, state):
        return self._images.get(
            piece_key,
            {},
        ).get(
            state,
            [],
        )
