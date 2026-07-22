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


class WaitingPlayer:
    __slots__ = (
        "user_id",
        "username",
        "rating",
        "connection_id",
        "session",
        "joined_at_ms",
    )

    def __init__(
        self,
        user_id,
        username,
        rating,
        connection_id,
        session,
        joined_at_ms,
    ):
        self.user_id = user_id
        self.username = username
        self.rating = rating
        self.connection_id = connection_id
        self.session = session
        self.joined_at_ms = joined_at_ms


class Matchmaker:
    """
    Queue of authenticated players waiting for a rated match.

    Matching is by ELO range. Does not create Match objects — the server does.
    """

    def __init__(self, elo_range=100, timeout_ms=60_000, clock=None):
        self._elo_range = elo_range
        self._timeout_ms = timeout_ms
        self._clock = clock if clock is not None else SystemClock()
        self._queue = []  # WaitingPlayer, FIFO

    @property
    def queue_size(self):
        return len(self._queue)

    def enqueue(self, session):
        """
        Add session to the queue, or return an immediate match pair.

        Returns:
            None if waiting, or (earlier_player, new_player) when matched.
            earlier_player should be White; new_player Black.
        """
        if session.user_id is None:
            raise ValueError("session must be authenticated")

        self.cancel(session.connection_id)
        self.cancel_user(session.user_id)

        candidate = WaitingPlayer(
            user_id=session.user_id,
            username=session.username,
            rating=session.rating if session.rating is not None else 1200,
            connection_id=session.connection_id,
            session=session,
            joined_at_ms=self._clock.now_ms(),
        )

        for index, waiting in enumerate(self._queue):
            if waiting.user_id == candidate.user_id:
                continue
            if abs(waiting.rating - candidate.rating) <= self._elo_range:
                self._queue.pop(index)
                return waiting, candidate

        self._queue.append(candidate)
        return None

    def cancel(self, connection_id):
        """Remove a waiter by connection_id. Returns True if removed."""
        for index, waiting in enumerate(self._queue):
            if waiting.connection_id == connection_id:
                self._queue.pop(index)
                return True
        return False

    def cancel_user(self, user_id):
        """Remove any waiter with this user_id (prevents self-match / dupes)."""
        removed = False
        kept = []
        for waiting in self._queue:
            if waiting.user_id == user_id:
                removed = True
            else:
                kept.append(waiting)
        self._queue = kept
        return removed

    def pop_expired(self):
        """
        Remove and return waiters who exceeded timeout_ms.

        Uses the injected clock — no real sleep.
        """
        now = self._clock.now_ms()
        expired = []
        kept = []
        for waiting in self._queue:
            if now - waiting.joined_at_ms >= self._timeout_ms:
                expired.append(waiting)
            else:
                kept.append(waiting)
        self._queue = kept
        return expired
