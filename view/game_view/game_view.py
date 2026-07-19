class GameView:
    """
    Creates and owns all visual components of the game.
    """

    def __init__(
        self,
        layout,
        board_mapper,
        renderer,
    ):
        self._layout = layout
        self._board_mapper = board_mapper
        self._renderer = renderer
        self._last_frame = None

    def render(self, snapshot):
        self._last_frame = self._renderer.render(snapshot)
        return self._last_frame

    @property
    def board_mapper(self):
        return self._board_mapper

    @property
    def layout(self):
        return self._layout

    @property
    def last_frame(self):
        return self._last_frame