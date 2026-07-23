"""Unit tests for GameMessageHandler."""

import pytest

from server.handlers.game_message_handler import GameMessageHandler
from server.session_role_enum import SessionRole
from shared.protocol import SPECTATOR_READ_ONLY, decode_message


class _FakeWs:
    def __init__(self):
        self.sent = []

    async def send(self, raw):
        self.sent.append(raw)


class _Session:
    def __init__(self, **kwargs):
        self.role = kwargs.get("role")
        self.is_in_game = kwargs.get("is_in_game", False)
        self.disconnected = kwargs.get("disconnected", False)
        self.game_id = kwargs.get("game_id", "g1")
        self.assigned_color = kwargs.get("assigned_color", "w")
        self.user_id = kwargs.get("user_id", 1)
        self.websocket = kwargs.get("websocket")


@pytest.mark.asyncio
async def test_spectator_move_rejected():
    ws = _FakeWs()
    session = _Session(role=SessionRole.SPECTATOR, is_in_game=True, websocket=ws)
    sessions = {ws: session}
    handler = GameMessageHandler(
        sessions,
        registry={},
        command_handler=None,
        default_game_id="default",
        rooms=None,
        broadcast_room_update_fn=None,
        discard_incomplete_fn=None,
        finalize_game_over_fn=None,
    )
    await handler.handle_move(ws, {"type": "move", "payload": {"command": "WPe2e4"}})
    assert len(ws.sent) == 1
    err = decode_message(ws.sent[0])
    assert err["payload"]["code"] == SPECTATOR_READ_ONLY


@pytest.mark.asyncio
async def test_active_player_move_accepted():
    ws = _FakeWs()
    session = _Session(role=SessionRole.PLAYER, is_in_game=True, websocket=ws)

    class _Match:
        def __init__(self):
            self.lock = _AsyncLock()

        def player_for_color(self, color):
            return session

        async def broadcast_snapshot(self):
            pass

    class _AsyncLock:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

    class _Commands:
        def apply_move_command(self, match, command, assigned_color=None):
            return {
                "ok": True,
                "command": command,
                "snapshot": {"pieces": []},
            }

    match = _Match()
    handler = GameMessageHandler(
        {ws: session},
        registry={"g1": match},
        command_handler=_Commands(),
        default_game_id="default",
        rooms=None,
        broadcast_room_update_fn=None,
        discard_incomplete_fn=None,
        finalize_game_over_fn=None,
    )
    await handler.handle_move(ws, {"type": "move", "payload": {"command": "WPe2e4"}})
    assert any("move_accepted" in raw for raw in ws.sent)
