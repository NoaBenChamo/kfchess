"""Unit tests for MessageRouter (decode / ping / dispatch only)."""

import pytest

from server.message_router import MessageRouter
from shared.protocol import encode_message


class _FakeWs:
    def __init__(self):
        self.sent = []

    async def send(self, raw):
        self.sent.append(raw)


@pytest.mark.asyncio
async def test_router_dispatches_known_type():
    seen = []

    async def on_login(websocket, message):
        seen.append((websocket, message["type"]))

    router = MessageRouter({"login": on_login})
    ws = _FakeWs()
    await router.handle_raw(ws, encode_message("login", {"username": "a", "password": "b"}))
    assert len(seen) == 1
    assert seen[0][1] == "login"
    assert ws.sent == []


@pytest.mark.asyncio
async def test_router_unsupported_type_sends_error():
    router = MessageRouter({})
    ws = _FakeWs()
    await router.handle_raw(ws, encode_message("nope", {}))
    assert len(ws.sent) == 1
    assert "unsupported type: nope" in ws.sent[0]
    assert "INVALID_MESSAGE" in ws.sent[0]


@pytest.mark.asyncio
async def test_router_ping_returns_pong():
    router = MessageRouter({})
    ws = _FakeWs()
    await router.handle_raw(ws, encode_message("ping", {}))
    assert len(ws.sent) == 1
    assert '"type": "pong"' in ws.sent[0] or '"type":"pong"' in ws.sent[0].replace(" ", "")


@pytest.mark.asyncio
async def test_router_protocol_error_on_bad_json():
    router = MessageRouter({})
    ws = _FakeWs()
    await router.handle_raw(ws, "{not-json")
    assert len(ws.sent) == 1
    assert "INVALID_MESSAGE" in ws.sent[0]
