class FrameClock:
    """
    Tracks elapsed UI time for deterministic animation frame selection.

    Separate from game engine time so renderers never call wall-clock APIs.
    """

    def __init__(self, start_ms=0):
        self._elapsed_ms = start_ms

    def tick(self, delta_ms):
        if delta_ms > 0:
            self._elapsed_ms += delta_ms

    def now_ms(self):
        return self._elapsed_ms

    def reset(self, start_ms=0):
        self._elapsed_ms = start_ms
