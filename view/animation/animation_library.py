class AnimationLibrary:
    """
    Provides animation frames for every piece and state.

    This class hides the AssetsManager from the rest of the view layer.
    """

    def __init__(self, assets_manager):
        self._assets_manager = assets_manager

    def get_frames(self, piece_key, state):
        """
        Returns the animation frames for the given piece and state.

        Args:
            piece_key: Example "wQ", "bN".
            state: PieceState.

        Returns:
            List[Img]
        """
        return self._assets_manager.get_piece_frames(
            piece_key,
            state,
        )