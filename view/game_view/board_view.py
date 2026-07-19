import time
import cv2
import numpy as np
from img import Img
from model.piece_state import PieceState
from config.constants import (
    BOARD_COLS, BOARD_ROWS,
    LABEL_MARGIN, FRAME_DURATION_MS,
)


class BoardView:

    def __init__(self, board_rect, canvas_width, canvas_height, assets_manager):
        self._board_rect = board_rect
        self._canvas_width = canvas_width
        self._canvas_height = canvas_height
        self._cell_width = board_rect.cell_width
        self._cell_height = board_rect.cell_height
        self._label_margin = LABEL_MARGIN
        self._canvas = None
        self._clean_canvas = None
        self._assets_manager = assets_manager
        self._create_canvas()

    def _create_canvas(self):
        """Build the local board surface from immutable visual assets."""
        board = self._assets_manager.get_board().img
        channels = board.shape[2]
        canvas = np.zeros(
            (self._canvas_height, self._canvas_width, channels), dtype=np.uint8
        )
        board_h, board_w = board.shape[:2]
        canvas[:board_h, self._label_margin:self._label_margin + board_w] = board
        self._canvas = Img()
        self._canvas.img = canvas
        self._draw_labels()
        self._clean_canvas = canvas.copy()


    def clear(self):
        self._canvas.img = self._clean_canvas.copy()


    def _draw_labels(self):
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = max(0.3, self._cell_height / 200.0)
        color = (255, 255, 255, 255)
        thickness = 1

        for col in range(BOARD_COLS):
            letter = chr(ord("A") + col)
            x = self._label_margin + col * self._cell_width + self._cell_width // 2 - 5
            y = self._canvas_height - 6
            cv2.putText(
                self._canvas.img, letter, (x, y),
                font, font_scale, color, thickness, cv2.LINE_AA,
            )

        for row in range(BOARD_ROWS):
            number = str(BOARD_ROWS - row)
            x = 4
            y = row * self._cell_height + self._cell_height // 2 + 5
            cv2.putText(
                self._canvas.img, number, (x, y),
                font, font_scale, color, thickness, cv2.LINE_AA,
            )


    def render(self, snapshot):
        self.clear()
        self._draw_pieces(snapshot)
        self._draw_selection(snapshot)
        if snapshot.game_over:
            self._draw_game_over()


    def get_canvas(self):
        return self._canvas


    def _draw_pieces(self, snapshot):
        frame_index = self._current_frame()

        for piece in snapshot.pieces:
            local_x, local_y = self._piece_position_to_local(piece)

            piece_key = piece.color + piece.piece_type
            self._draw_piece(piece_key, piece.state, frame_index, local_x, local_y)

            if piece.rest_progress is not None:
                self._draw_cooldown(local_x, local_y, piece.rest_progress)

    def _draw_piece(self, piece_key, state, frame_index, x, y):
        frames = self._assets_manager.get_piece_frames(piece_key, state)
        if not frames:
            return
        frames[frame_index % len(frames)].draw_on(self._canvas, x, y)


    def _current_frame(self):
        return int(time.time() * 1000) // FRAME_DURATION_MS

    def _position_to_local(self, position):
        """Map a model Position to this view's own local canvas."""
        return (
            self._label_margin + position.col * self._cell_width,
            position.row * self._cell_height,
        )

    def _piece_position_to_local(self, piece):
        x, y = self._position_to_local(piece.position)
        progress = piece.progress

        if piece.state == PieceState.MOVE and piece.target is not None:
            target_x, target_y = self._position_to_local(piece.target)
            x += int((target_x - x) * progress)
            y += int((target_y - y) * progress)
        elif piece.state == PieceState.JUMP and progress is not None:
            jump_height = max(1, int(self._cell_height * 0.4))
            y -= int(jump_height * 4 * progress * (1 - progress))

        return x, y


    def _draw_selection(self, snapshot):
        if snapshot.selected_cell is None:
            return

        x, y = self._position_to_local(snapshot.selected_cell)

        overlay = np.zeros(
            (self._cell_height, self._cell_width, 4), dtype=np.uint8
        )
        overlay[:, :] = (0, 255, 255, 80)

        selection = Img()
        selection.img = overlay
        selection.draw_on(self._canvas, x, y)


    def _draw_cooldown(self, x, y, progress):
        bar_h = max(4, self._cell_height // 10)
        bar_w = self._cell_width - 8
        filled_w = int(bar_w * progress)

        bar = np.zeros((bar_h, bar_w, 4), dtype=np.uint8)
        bar[:, :] = (40, 40, 40, 180)

        if filled_w > 0:
            red = int(255 * (1.0 - progress))
            green = int(200 * progress + 55)
            bar[:, :filled_w] = (0, green, red, 220)

        overlay = Img()
        overlay.img = bar
        overlay.draw_on(
            self._canvas,
            x + 4,
            y + self._cell_height - bar_h - 2,
        )


    def _draw_game_over(self):
        h, w = self._canvas.img.shape[:2]
        font_scale = max(1.0, w / 400.0)
        self._canvas.put_text(
            "GAME OVER",
            w // 4,
            h // 2,
            font_scale,
            color=(0, 0, 255, 255),
            thickness=4,
        )
