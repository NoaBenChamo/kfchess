# The object that the view receives from the backend.
class PieceSnapshot:

    def __init__(
        self,
        color,
        piece_type,
        position,
        state,
        target=None,
        progress=None,
        rest_progress=None,
    ):
        self.color = color
        self.piece_type = piece_type
        self.position = position
        self.state = state
        self.target = target
        self.progress = progress
        self.rest_progress = rest_progress
