from model.piece_state import PieceState


class PieceRenderer:
    """
    Draws all chess pieces.

    Responsible for:
        - computing each piece's visual position
        - interpolating movement
        - drawing jump arcs
        - drawing the current animation frame

    Does not know how animation frames are selected.
    """

    def __init__(self, board_geometry, piece_animator):
        self._geometry = board_geometry
        self._piece_animator = piece_animator

        self._cell_width = board_geometry.cell_width
        self._cell_height = board_geometry.cell_height

    def render(self, canvas, pieces, animation_time_ms):
        """
        Draw all pieces.
        """
        for piece in pieces:
            frame = self._piece_animator.current_frame(
                piece,
                animation_time_ms,
            )

            if frame is None:
                continue

            x, y = self._piece_position(piece)

            frame.draw_on(canvas, x, y)

    def _piece_position(self, piece):
        """
        Returns the current visual position of a piece.
        """
        x, y = self._geometry.position_to_local(piece.position)

        progress = self._progress(piece.progress)

        if (
            piece.state == PieceState.MOVE
            and piece.target is not None
        ):
            target_x, target_y = self._geometry.position_to_local(
                piece.target
            )

            x += int((target_x - x) * progress)
            y += int((target_y - y) * progress)

        elif piece.state == PieceState.JUMP:
            y -= self._jump_offset(progress)

        return x, y

    def _jump_offset(self, progress):
        """
        Computes the vertical offset for a jump animation.
        """
        jump_height = max(
            1,
            int(self._cell_height * 0.4),
        )

        return int(
            jump_height
            * 4
            * progress
            * (1.0 - progress)
        )

    @staticmethod
    def _progress(progress):
        if progress is None:
            return 0.0

        return max(
            0.0,
            min(1.0, progress),
        )