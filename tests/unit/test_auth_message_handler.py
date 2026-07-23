"""Unit tests for AuthMessageHandler."""

import pytest

from server.auth_service import AuthError
from server.handlers.auth_message_handler import AuthMessageHandler
from shared.protocol import decode_message


class _FakeWs:
    def __init__(self):
        self.sent = []

    async def send(self, raw):
        self.sent.append(raw)


class _Session:
    def __init__(self):
        self.is_authenticated = False
        self.connection_id = "c1"
        self.user_id = None
        self.username = None
        self.rating = None

    def set_user(self, user_id, username, rating):
        self.is_authenticated = True
        self.user_id = user_id
        self.username = username
        self.rating = rating


class _User:
    def __init__(self):
        self.id = 7
        self.username = "Alice"
        self.rating = 1200


class _Auth:
    def login(self, username, password):
        if password != "ok":
            raise AuthError("INVALID_CREDENTIALS", "bad")
        return _User()

    def register(self, username, password):
        return _User()


@pytest.mark.asyncio
async def test_login_calls_restore():
    ws = _FakeWs()
    session = _Session()
    restored = []

    async def restore(s):
        restored.append(s)

    handler = AuthMessageHandler({ws: session}, _Auth(), restore_fn=restore)
    await handler.handle_login(
        ws, {"type": "login", "payload": {"username": "Alice", "password": "ok"}}
    )
    assert session.is_authenticated
    assert restored == [session]
    assert any("auth_ok" in raw for raw in ws.sent)


@pytest.mark.asyncio
async def test_login_failure_does_not_restore():
    ws = _FakeWs()
    session = _Session()
    restored = []

    async def restore(s):
        restored.append(s)

    handler = AuthMessageHandler({ws: session}, _Auth(), restore_fn=restore)
    await handler.handle_login(
        ws, {"type": "login", "payload": {"username": "Alice", "password": "no"}}
    )
    assert restored == []
    err = decode_message(ws.sent[0])
    assert err["payload"]["code"] == "INVALID_CREDENTIALS"
