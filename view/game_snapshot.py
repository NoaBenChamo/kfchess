class GameSnapshot:
    """Immutable data holder describing the full visual state of the board at a point in time."""

    def __init__(self, piece_snapshots, selected_position, is_game_over):
        self.piece_snapshots = piece_snapshots
        self.selected_position = selected_position
        self.is_game_over = is_game_over
