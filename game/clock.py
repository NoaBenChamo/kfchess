class GameClock:

    def __init__(self):
        self._time = 0

    def advance(self, ms):
        self._time += ms

    def get_time(self):
        return self._time