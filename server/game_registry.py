class GameRegistry:
    """Maps game_id -> Match. Routing always goes through the registry."""

    def __init__(self):
        self._matches = {}

    def register(self, match):
        self._matches[match.game_id] = match

    def get(self, game_id):
        return self._matches.get(game_id)

    def create_default(self):
        from server.match import Match

        match = Match("default")
        self.register(match)
        return match

    def all_matches(self):
        return list(self._matches.values())

    def __contains__(self, game_id):
        return game_id in self._matches

    def __len__(self):
        return len(self._matches)
