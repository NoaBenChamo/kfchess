class PieceSnapshot:
    """Immutable data holder describing a single piece's visual state at a point in time."""

    def __init__(self, color, piece_type, row, col, progress):
        self.color = color
        self.piece_type = piece_type
        self.row = row
        self.col = col
        self.progress = progress
