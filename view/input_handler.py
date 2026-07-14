class InputHandler:
    """Translates raw input events into controller calls."""

    def __init__(self, controller):
        self._controller = controller

    def handle(self, event):
        """Process a single input event and forward it to the controller."""
        pass
