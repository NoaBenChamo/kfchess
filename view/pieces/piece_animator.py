from config.constants import FRAME_DURATION_MS


class PieceAnimator:
    """
    Selects the correct animation frame for a chess piece.

    This class knows nothing about board geometry or rendering.
    """

    def __init__(self, animation_library):
        self._animation_library = animation_library

    def current_frame(self, piece, animation_time_ms):
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

        frame_index = animation_time_ms // FRAME_DURATION_MS

        return frames[frame_index % len(frames)]

    @staticmethod
    def frame_index(animation_time_ms):
        return animation_time_ms // FRAME_DURATION_MS
