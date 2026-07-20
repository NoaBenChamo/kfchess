class MoveRecord:
    """
    Immutable record of a single completed move, used only for display.

    move_type values:
        'move'    — regular move to an empty square
        'capture' — move that takes an enemy piece
        'jump'    — piece lifted in place (right-click)
    """

    def __init__(
        self,
        color,
        piece_type,
        source,
        target,
        move_type="move",
        time_ms=None,
    ):
        self.color = color
        self.piece_type = piece_type
        self.source = source
        self.target = target
        self.move_type = move_type
        self.time_ms = time_ms

    def __str__(self):
        cols = "ABCDEFGH"
        rows = "87654321"

        def fmt(pos):
            return cols[pos.col] + rows[pos.row]

        if self.move_type == "jump":
            return f"{self.piece_type}{fmt(self.source)} →"

        sep = "x" if self.move_type == "capture" else "-"
        return f"{self.piece_type}{fmt(self.source)}{sep}{fmt(self.target)}"
