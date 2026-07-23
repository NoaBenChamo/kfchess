"""Unit tests for MatchmakingHandler expire path."""

import pytest

from server.handlers.matchmaking_handler import MatchmakingHandler


class _FakeWs:
    def __init__(self):
        self.sent = []

    async def send(self, raw):
        self.sent.append(raw)


class _Waiting:
    def __init__(self, ws):
        self.connection_id = "c1"
        self.session = type("S", (), {"websocket": ws})()


class _Matchmaker:
    def __init__(self, waiting):
        self._waiting = waiting

    def pop_expired(self):
        items = self._waiting
        self._waiting = []
        return items

    def cancel(self, connection_id):
        return False

    def enqueue(self, session):
        return None


@pytest.mark.asyncio
async def test_expire_matchmaking_notifies_waiter():
    ws = _FakeWs()
    handler = MatchmakingHandler(
        {},
        registry=type("R", (), {"all_matches": lambda self: []})(),
        matchmaker=_Matchmaker([_Waiting(ws)]),
        create_match_fn=None,
        start_tick_if_running_fn=None,
        start_rated_fn=None,
    )
    await handler.expire_matchmaking()
    assert len(ws.sent) == 1
    assert "matchmaking_timeout" in ws.sent[0]
