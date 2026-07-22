"""Unit tests for Match disconnect grace with FakeClock."""

import pytest

from server.clock import FakeClock
from server.match import Match


@pytest.mark.asyncio
async def test_match_grace_expires_via_fake_clock_without_real_sleep():
    clock = FakeClock(start_ms=0)
    match = Match("g_test", clock=clock)
    match.set_grace_ms(1_000)

    expired = []

    async def on_expire(m, color):
        expired.append((m.game_id, color))

    match.begin_disconnect_grace("w", on_expire=on_expire, grace_ms=1_000)
    assert match.pop_expired_graces() == []

    clock.advance(999)
    assert match.pop_expired_graces() == []

    clock.advance(1)
    assert match.pop_expired_graces() == ["w"]
    # Deadline consumed — second pop is empty.
    assert match.pop_expired_graces() == []


def test_cancel_grace_removes_deadline():
    clock = FakeClock()
    match = Match("g_test", clock=clock)
    match.begin_disconnect_grace("b", grace_ms=500)
    match.cancel_grace("b")
    clock.advance(1_000)
    assert match.pop_expired_graces() == []
