import time

from config.constants import FRAME_DURATION_MS


class PieceAnimator:
    """
    Responsible for selecting the correct animation frame
    for a specific chess piece.

    This class knows nothing about board geometry or rendering.
    """

    def __init__(self, animation_library):
        self._animation_library = animation_library

    def current_frame(self, piece):
        """
        Returns the image that should currently be displayed
        for the given piece.
        """
        piece_key = piece.color + piece.piece_type

        frames = self._animation_library.get_frames(
            piece_key,
            piece.state,
        )

        if not frames:
            return None

        frame_index = self._current_frame_index()

        return frames[frame_index % len(frames)]

    @staticmethod
    def _current_frame_index():
        return (
            int(time.time() * 1000)
            // FRAME_DURATION_MS
        )
