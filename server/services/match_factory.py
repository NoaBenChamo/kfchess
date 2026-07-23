"""Create and configure Match instances."""

from server.match import Match


class MatchFactory:
    """Create a Match and wire clock / grace / end-of-game callbacks."""

    def __init__(self, clock, grace_ms, on_game_over, on_grace_expired):
        self._clock = clock
        self._grace_ms = grace_ms
        self._on_game_over = on_game_over
        self._on_grace_expired = on_grace_expired

    def configure(self, match):
        match.set_clock(self._clock)
        match.set_grace_ms(self._grace_ms)
        match.set_game_over_handler(self._on_game_over)
        match.set_grace_expire_handler(self._on_grace_expired)

    def create(self, game_id):
        match = Match(game_id, clock=self._clock)
        self.configure(match)
        return match
