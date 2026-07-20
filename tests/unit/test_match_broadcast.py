import asyncio

import pytest

from server.game_command_handler import GameCommandHandler
from server.match import Match
from shared.protocol import decode_message


class _RecordingSocket:
    def __init__(self):
        self.sent = []

    async def send(self, raw):
        self.sent.append(raw)


@pytest.mark.asyncio
async def test_broadcast_reaches_only_this_match_connections():
    match_a = Match("a")
    match_b = Match("b")
    socket_a = _RecordingSocket()
    socket_b = _RecordingSocket()
    match_a.add_connection(socket_a)
    match_b.add_connection(socket_b)

    match_a.bump_sequence()
    await match_a.broadcast_snapshot()

    assert len(socket_a.sent) == 1
    assert len(socket_b.sent) == 0
    message = decode_message(socket_a.sent[0])
    assert message["type"] == "state_snapshot"
    assert message["payload"]["sequence"] == 1


@pytest.mark.asyncio
async def test_both_peers_on_same_match_receive_broadcast():
    match = Match("default")
    peer_a = _RecordingSocket()
    peer_b = _RecordingSocket()
    match.add_connection(peer_a)
    match.add_connection(peer_b)

    handler = GameCommandHandler()
    async with match.lock:
        result = handler.apply_move_command(match, "WPe2e4")
    assert result["ok"] is True

    await match.broadcast_snapshot()

    assert len(peer_a.sent) == 1
    assert len(peer_b.sent) == 1
    snap_a = decode_message(peer_a.sent[0])
    snap_b = decode_message(peer_b.sent[0])
    assert snap_a == snap_b
    assert snap_a["payload"]["sequence"] == result["snapshot"]["sequence"]
