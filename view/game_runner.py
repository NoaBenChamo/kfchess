class GameRunner:
    """Owns the main loop: ticks the clock, collects input, and triggers rendering."""

    def __init__(self, controller, renderer, input_handler):
        self._controller = controller
        self._renderer = renderer
        self._input_handler = input_handler
        self._running = False

    def run(self):
        """Start the main game loop."""
        pass
