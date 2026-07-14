class Renderer:
    """Draws the current game snapshot onto the display surface."""

    def __init__(self, surface, image_view):
        self._surface = surface
        self._image_view = image_view

    def render(self, snapshot):
        """Draw the full board state described by the given snapshot."""
        pass
