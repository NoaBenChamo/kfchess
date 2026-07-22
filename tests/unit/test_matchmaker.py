from server.matchmaker import FakeClock, Matchmaker


class _FakeSession:
    def __init__(self, user_id, username, rating, connection_id):
        self.user_id = user_id
        self.username = username
        self.rating = rating
        self.connection_id = connection_id


def test_match_within_elo_range():
    mm = Matchmaker(elo_range=100, clock=FakeClock())
    first = _FakeSession(1, "Alice", 1200, "c1")
    second = _FakeSession(2, "Bob", 1250, "c2")

    assert mm.enqueue(first) is None
    pair = mm.enqueue(second)

    assert pair is not None
    earlier, newer = pair
    assert earlier.username == "Alice"
    assert newer.username == "Bob"
    assert mm.queue_size == 0


def test_no_match_outside_elo_range():
    mm = Matchmaker(elo_range=100, clock=FakeClock())
    mm.enqueue(_FakeSession(1, "Alice", 1200, "c1"))
    pair = mm.enqueue(_FakeSession(2, "Bob", 1400, "c2"))

    assert pair is None
    assert mm.queue_size == 2


def test_cannot_match_same_user_twice():
    mm = Matchmaker(elo_range=100, clock=FakeClock())
    mm.enqueue(_FakeSession(1, "Alice", 1200, "c1"))
    # Same user_id, new connection — replaces previous waiter, no self-match.
    pair = mm.enqueue(_FakeSession(1, "Alice", 1200, "c2"))
    assert pair is None
    assert mm.queue_size == 1


def test_matched_players_removed_atomically():
    mm = Matchmaker(elo_range=100, clock=FakeClock())
    mm.enqueue(_FakeSession(1, "Alice", 1200, "c1"))
    mm.enqueue(_FakeSession(3, "Carol", 1500, "c3"))  # out of range, stays
    pair = mm.enqueue(_FakeSession(2, "Bob", 1200, "c2"))

    assert pair is not None
    assert mm.queue_size == 1
    assert mm._queue[0].username == "Carol"


def test_timeout_uses_injected_clock_without_sleep():
    clock = FakeClock(start_ms=0)
    mm = Matchmaker(elo_range=100, timeout_ms=1000, clock=clock)
    mm.enqueue(_FakeSession(1, "Alice", 1200, "c1"))

    clock.advance(999)
    assert mm.pop_expired() == []
    assert mm.queue_size == 1

    clock.advance(1)
    expired = mm.pop_expired()
    assert len(expired) == 1
    assert expired[0].username == "Alice"
    assert mm.queue_size == 0


def test_cancel_removes_waiter():
    mm = Matchmaker(elo_range=100, clock=FakeClock())
    mm.enqueue(_FakeSession(1, "Alice", 1200, "c1"))
    assert mm.cancel("c1") is True
    assert mm.queue_size == 0
