"""Unit tests for ConnectionLifecycleService."""

import pytest

from server.services.connection_lifecycle_service import ConnectionLifecycleService
from server.session_role_enum import SessionRole


class _Matchmaker:
    def __init__(self):
        self.cancelled = []

    def cancel(self, connection_id):
        self.cancelled.append(connection_id)
        return True


class _Rooms:
    def __init__(self):
        self.discarded = []

    def get(self, room_id):
        return None

    def discard(self, room_id):
        self.discarded.append(room_id)

    def remove_user(self, room_id, user_id):
        pass


class _Registry:
    def __init__(self, matches=None):
        self._matches = matches or {}
        self.unregistered = []

    def get(self, game_id):
        return self._matches.get(game_id)

    def all_matches(self):
        return list(self._matches.values())

    def unregister(self, game_id):
        self.unregistered.append(game_id)
        self._matches.pop(game_id, None)


class _Match:
    def __init__(self, game_id="g1", room_id="ROOM01"):
        self.game_id = game_id
        self.room_id = room_id
        self.released = []
        self.stopped = False

    def player_count(self):
        return 1

    def release(self, websocket):
        self.released.append(websocket)

    async def stop(self):
        self.stopped = True

    def reconnect_user(self, session, user_id):
        return None


class _Session:
    def __init__(self):
        self.connection_id = "c1"
        self.game_id = "g1"
        self.user_id = 1
        self.is_in_game = True
        self.role = SessionRole.PLAYER


@pytest.mark.asyncio
async def test_discard_incomplete_waiting_room():
    match = _Match()
    registry = _Registry({"g1": match})
    rooms = _Rooms()
    service = ConnectionLifecycleService(
        registry,
        rooms,
        _Matchmaker(),
        default_game_id="default",
        disconnect_grace_ms=1000,
        on_grace_expired_fn=None,
        broadcast_room_update_fn=None,
    )
    session = _Session()
    ws = object()
    await service.discard_incomplete_match(match, ws, session)
    assert rooms.discarded == ["ROOM01"]
    assert match.stopped is True
    assert registry.unregistered == ["g1"]


@pytest.mark.asyncio
async def test_connection_lost_cancels_matchmaking():
    mm = _Matchmaker()
    service = ConnectionLifecycleService(
        _Registry(),
        _Rooms(),
        mm,
        default_game_id="default",
        disconnect_grace_ms=1000,
        on_grace_expired_fn=None,
        broadcast_room_update_fn=None,
    )
    session = _Session()
    session.game_id = None
    session.is_in_game = False
    session.role = None
    await service.on_connection_lost(session, object())
    assert mm.cancelled == ["c1"]
