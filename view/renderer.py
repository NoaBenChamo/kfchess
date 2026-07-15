import time
from input.board_mapper import BoardMapper

FRAME_DURATION_MS = 150


class Renderer:

    def __init__(self, image_view):
        self._image_view = image_view

    def render(self, snapshot):
        self._image_view.clear()
        self._draw_pieces(snapshot)
        self._draw_selection(snapshot)
        if snapshot.game_over:
            self._draw_game_over()
        self._image_view.present()

    def _draw_pieces(self, snapshot):
        current_ms = int(time.time() * 1000)
        for piece in snapshot.pieces:
            x, y = BoardMapper.to_pixels(piece.position)
            piece_key = piece.color + piece.piece_type
            frame = current_ms // FRAME_DURATION_MS
            self._image_view.draw_piece(piece_key, piece.state, frame, x, y)

    def _draw_selection(self, snapshot):
        if snapshot.selected_cell is None:
            return
        x, y = BoardMapper.to_pixels(snapshot.selected_cell)
        self._image_view.draw_selection(x, y)

    def _draw_game_over(self):
        self._image_view.draw_game_over()
