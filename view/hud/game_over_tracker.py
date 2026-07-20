class GameOverTracker:
    """
    Bus subscriber that records game-over for HUD / animation triggers.

    Separate from SoundPlayer so Stage A can prove two independent
    consumers react to GameOverEvent without the engine calling them.
    """

    def __init__(self):
        self.game_over = False
        self.notification_count = 0
        self.last_timestamp_ms = None

    def on_game_over(self, event):
        self.game_over = True
        self.notification_count += 1
        self.last_timestamp_ms = event.timestamp_ms
