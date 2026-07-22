import asyncio

import pytest
from websockets.asyncio.server import serve

from client.network_client import NetworkClient
from server.dal.database import Database
from server.game_server import GameServer


async def _start(grace_ms=200):
    database = Database(":memory:")
    database.connect()
    database.initialize_schema()
    game_server = GameServer(
        database=database,
        tick_ms=20,
        disconnect_grace_ms=grace_ms,
    )
    await game_server.start()
    server = await serve(game_server.handler, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    return game_server, server, port, database


async def _stop(game_server, server, database):
    server.close()
    await server.wait_closed()
    await game_server.stop()
    database.close()


async def _match_two_players(uri):
    client_a = NetworkClient(uri)
    client_b = NetworkClient(uri)
    await client_a.connect()
    await client_b.connect()
    await client_a.register("Alice", "secret1")
    await client_b.register("Bob", "secret1")
    waiting = await client_a.play_request()
    assert waiting["type"] == "request_ok"
    matched_b = await client_b.play_request()
    assert matched_b["type"] == "match_found"
    matched_a = await client_a.receive_until("match_found")
    await client_a.receive_until("state_snapshot")
    await client_b.receive_until("state_snapshot")
    return client_a, client_b, matched_a["payload"]["game_id"]


@pytest.mark.asyncio
async def test_reconnect_before_grace_keeps_game_alive():
    game_server, server, port, database = await _start(grace_ms=500)
    uri = f"ws://127.0.0.1:{port}"
    try:
        white, black, game_id = await _match_two_players(uri)

        await white.close()
        notice = await black.receive_until("player_disconnected")
        assert notice["payload"]["color"] == "w"
        assert notice["payload"]["grace_period_ms"] == 500

        # Reconnect as Alice before grace expires.
        restored = NetworkClient(uri)
        await restored.connect()
        auth = await restored.login("Alice", "secret1")
        assert auth["type"] == "auth_ok"
        found = await restored.receive_until("match_found")
        assert found["payload"]["game_id"] == game_id
        assert found["payload"]["color"] == "w"
        await restored.receive_until("state_snapshot")

        reconnected = await black.receive_until("player_reconnected")
        assert reconnected["payload"]["color"] == "w"

        move = await restored.send_move("WPe2e4")
        assert move["type"] == "move_accepted"

        await black.close()
        await restored.close()
    finally:
        await _stop(game_server, server, database)


@pytest.mark.asyncio
async def test_grace_timeout_resigns_once():
    game_server, server, port, database = await _start(grace_ms=100)
    uri = f"ws://127.0.0.1:{port}"
    try:
        white, black, _game_id = await _match_two_players(uri)
        await white.close()
        await black.receive_until("player_disconnected")

        over = await black.receive_until("game_over", timeout=2.0)
        assert over["payload"]["winner"] == "b"
        assert over["payload"]["reason"] in ("game_over", "king_captured")

        # Second wait should not deliver another game_over immediately.
        with pytest.raises(TimeoutError):
            await black.receive_until("game_over", timeout=0.3)

        await black.close()
    finally:
        await _stop(game_server, server, database)


@pytest.mark.asyncio
async def test_reconnect_after_game_over_does_not_revive():
    game_server, server, port, database = await _start(grace_ms=50)
    uri = f"ws://127.0.0.1:{port}"
    try:
        white, black, game_id = await _match_two_players(uri)
        await white.close()
        await black.receive_until("player_disconnected")
        await black.receive_until("game_over", timeout=2.0)
        await black.close()

        revived = NetworkClient(uri)
        await revived.connect()
        await revived.login("Alice", "secret1")
        # Should not get match_found for the finished game.
        with pytest.raises(TimeoutError):
            await revived.receive_until("match_found", timeout=0.4)
        await revived.close()

        assert game_server.registry.get(game_id) is not None
    finally:
        await _stop(game_server, server, database)
