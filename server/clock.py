import time


class SystemClock:
    """Wall-clock time in milliseconds."""

    def now_ms(self):
        return int(time.time() * 1000)


class FakeClock:
    """Injectable clock for unit tests (no real sleep)."""

    def __init__(self, start_ms=0):
        self._now = start_ms

    def now_ms(self):
        return self._now

    def advance(self, ms):
        self._now += ms
