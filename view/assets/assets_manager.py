import os
import warnings

import cv2
import numpy as np

from img import Img
from config.constants import (
    VALID_COLORS,
    VALID_PIECES,
    ASSETS_DIR,
)
from model.piece_state import PieceState


class AssetsManager:
    """
    Loads and caches board and piece sprites for the view layer.

    Missing piece sprites fall back to idle frames, then to a placeholder.
    A missing board image raises an error during initialization.
    """

    PLACEHOLDER_COLORS = {
        "w": (200, 200, 200, 255),
        "b": (80, 80, 80, 255),
    }

    def __init__(self, board_rect):
        self._board_rect = board_rect
        self._cell_width = board_rect.cell_width
        self._cell_height = board_rect.cell_height

        self._board = None
        self._images = {}
        self._placeholders = {}

        self._load_board()
        self._load_pieces()

    def _load_board(self):
        board_path = os.path.join(
            ASSETS_DIR,
            "board.png",
        )

        if not os.path.isfile(board_path):
            raise FileNotFoundError(
                f"Board image not found: {board_path}"
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
            frames = self._load_state_frames(piece_key, state)
            if not frames:
                warnings.warn(
                    f"Missing sprites for {piece_key}/{state.value}",
                    stacklevel=2,
                )
            self._images[piece_key][state] = frames

        idle_frames = self._images[piece_key][PieceState.IDLE]
        if not idle_frames:
            idle_frames = [self._get_placeholder(piece_key)]
            self._images[piece_key][PieceState.IDLE] = idle_frames
            warnings.warn(
                f"Using placeholder for {piece_key} idle sprites",
                stacklevel=2,
            )

        for state in PieceState:
            if not self._images[piece_key][state]:
                self._images[piece_key][state] = list(idle_frames)

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

    def _get_placeholder(self, piece_key):
        if piece_key in self._placeholders:
            return self._placeholders[piece_key]

        color = piece_key[0]
        fill = self.PLACEHOLDER_COLORS.get(
            color,
            (128, 128, 128, 255),
        )

        image = np.zeros(
            (self._cell_height, self._cell_width, 4),
            dtype=np.uint8,
        )
        image[:, :] = fill

        piece_label = piece_key[1]
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = max(0.4, self._cell_height / 120.0)
        thickness = max(1, int(font_scale * 2))

        text_size, _ = cv2.getTextSize(
            piece_label,
            font,
            font_scale,
            thickness,
        )

        text_x = (self._cell_width - text_size[0]) // 2
        text_y = (self._cell_height + text_size[1]) // 2

        cv2.putText(
            image,
            piece_label,
            (text_x, text_y),
            font,
            font_scale,
            (255, 255, 255, 255),
            thickness,
            cv2.LINE_AA,
        )

        placeholder = Img()
        placeholder.img = image
        self._placeholders[piece_key] = placeholder

        return placeholder

    def get_board(self):
        return self._board

    def get_piece_frames(self, piece_key, state):
        frames = self._images.get(
            piece_key,
            {},
        ).get(
            state,
            [],
        )

        if frames:
            return frames

        return [self._get_placeholder(piece_key)]
