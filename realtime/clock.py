class GameClock:

    def __init__(self):
        self._time = 0


    # מקדם את השעון ב-ms מילישניות
    def advance(self, ms):
        self._time += ms


    # מחזיר את הזמן הנוכחי של השעון
    def get_time(self):
        return self._time