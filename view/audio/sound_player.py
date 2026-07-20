"""Bus-driven sound reactions. Missing platforms fail silently."""


class SoundPlayer:
    """
    Subscribes to lifecycle events and plays short cues when possible.

    Keeps a `played` log so tests can verify bus wiring without audio.
    """

    def __init__(self):
        self.played = []

    def on_game_started(self, event):
        self.played.append(("game_started",))
        self._beep(frequency=900, duration_ms=80)

    def on_game_over(self, event):
        self.played.append(("game_over", event.timestamp_ms))
        self._beep(frequency=400, duration_ms=200)

    @staticmethod
    def _beep(frequency, duration_ms):
        try:
            import winsound

            winsound.Beep(frequency, duration_ms)
        except Exception:
            pass
