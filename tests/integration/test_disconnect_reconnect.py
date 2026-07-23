"""Disconnect / reconnect policy tests (FakeClock for grace expiry)."""

import asyncio

import pytest
from websockets.asyncio.server import serve

from client.network_client import NetworkClient
from server.clock import FakeClock
from server.dal.database import Database
from server.game_server import GameServer
from server.session_role_enum import SessionRole
from shared.protocol import ROOM_NOT_FOUND


async def _start(grace_ms=1_000, clock=None, tick_ms=20):
    database = Database(":memory:")
    database.connect()
    database.initialize_schema()
    game_server = GameServer(
        database=database,
        tick_ms=tick_ms,
        disconnect_grace_ms=grace_ms,
        clock=clock,
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


async def _await_grace_expiry(clock, grace_ms, black):
    """Advance FakeClock past grace; wait for game_over via the tick loop."""
    clock.advance(grace_ms + 1)
    return await black.receive_until("game_over", timeout=2.0)


@pytest.mark.asyncio
async def test_disconnect_while_queued_removes_from_matchmaking():
    game_server, server, port, database = await _start()
    uri = f"ws://127.0.0.1:{port}"
    try:
        alice = NetworkClient(uri)
        await alice.connect()
        await alice.register("Alice", "secret1")
        waiting = await alice.play_request()
        assert waiting["type"] == "request_ok"
        assert game_server.matchmaker.queue_size == 1

        await alice.close()
        await asyncio.sleep(0.05)
        assert game_server.matchmaker.queue_size == 0
        assert len(game_server._sessions) == 0

        bob = NetworkClient(uri)
        await bob.connect()
        await bob.register("Bob", "secret1")
        response = await bob.play_request()
        assert response["type"] == "request_ok"
        assert game_server.matchmaker.queue_size == 1
        await bob.close()
    finally:
        await _stop(game_server, server, database)


@pytest.mark.asyncio
async def test_room_creator_disconnect_before_join_invalidates_code():
    game_server, server, port, database = await _start()
    uri = f"ws://127.0.0.1:{port}"
    try:
        creator = NetworkClient(uri)
        await creator.connect()
        await creator.register("Alice", "secret1")
        room = await creator.create_room()
        room_id = room["payload"]["room_id"]
        game_id = room["payload"]["game_id"]
        assert game_server.rooms.get(room_id) is not None

        await creator.close()
        await asyncio.sleep(0.05)

        assert game_server.rooms.get(room_id) is None
        assert game_server.registry.get(game_id) is None

        joiner = NetworkClient(uri)
        await joiner.connect()
        await joiner.register("Bob", "secret1")
        failed = await joiner.join_room(room_id)
        assert failed["type"] == "error"
        assert failed["payload"]["code"] == ROOM_NOT_FOUND
        await joiner.close()
    finally:
        await _stop(game_server, server, database)


@pytest.mark.asyncio
async def test_player_disconnect_before_game_start_no_solo_board():
    """Creator leaves waiting room — no grace, no ghost seat for a later joiner."""
    game_server, server, port, database = await _start(grace_ms=5_000)
    uri = f"ws://127.0.0.1:{port}"
    try:
        creator = NetworkClient(uri)
        await creator.connect()
        await creator.register("Alice", "secret1")
        room = await creator.create_room()
        room_id = room["payload"]["room_id"]
        await creator.close()
        await asyncio.sleep(0.05)

        # No grace broadcast path — room is gone, not a disconnected white seat.
        assert game_server.rooms.get(room_id) is None
        for match in game_server.registry.all_matches():
            if match.game_id == "default":
                continue
            assert match.player_count() == 0
    finally:
        await _stop(game_server, server, database)


@pytest.mark.asyncio
async def test_player_disconnect_during_active_game_notifies_opponent():
    clock = FakeClock()
    game_server, server, port, database = await _start(grace_ms=5_000, clock=clock)
    uri = f"ws://127.0.0.1:{port}"
    try:
        white, black, game_id = await _match_two_players(uri)
        await white.close()
        notice = await black.receive_until("player_disconnected")
        assert notice["payload"]["color"] == "w"
        assert notice["payload"]["grace_period_ms"] == 5_000
        match = game_server.registry.get(game_id)
        assert match.player_for_color("w").disconnected is True
        assert match.player_count() == 2
        await black.close()
    finally:
        await _stop(game_server, server, database)


@pytest.mark.asyncio
async def test_reconnect_during_grace_restores_seat_and_replaces_connection():
    clock = FakeClock()
    game_server, server, port, database = await _start(grace_ms=60_000, clock=clock)
    uri = f"ws://127.0.0.1:{port}"
    try:
        white, black, game_id = await _match_two_players(uri)
        await white.send_move("WPe2e4")
        await black.receive_until("state_snapshot")

        await white.close()
        await black.receive_until("player_disconnected")

        restored = NetworkClient(uri)
        await restored.connect()
        auth = await restored.login("Alice", "secret1")
        assert auth["type"] == "auth_ok"
        found = await restored.receive_until("match_found")
        assert found["payload"]["game_id"] == game_id
        assert found["payload"]["color"] == "w"
        snap = await restored.receive_until("state_snapshot")
        assert len(snap["payload"].get("white_moves") or []) >= 1

        reconnected = await black.receive_until("player_reconnected")
        assert reconnected["payload"]["color"] == "w"

        match = game_server.registry.get(game_id)
        white_seat = match.player_for_color("w")
        assert white_seat is not None
        assert white_seat.disconnected is False
        assert white_seat.user_id == auth["payload"]["user_id"]
        # Exactly one white seat — no duplicate player.
        assert match.player_count() == 2

        move = await restored.send_move("WNg1f3")
        assert move["type"] == "move_accepted"

        await black.close()
        await restored.close()
    finally:
        await _stop(game_server, server, database)


@pytest.mark.asyncio
async def test_reconnect_after_grace_timeout_is_technical_loss():
    clock = FakeClock()
    grace_ms = 1_000
    game_server, server, port, database = await _start(grace_ms=grace_ms, clock=clock)
    uri = f"ws://127.0.0.1:{port}"
    try:
        white, black, game_id = await _match_two_players(uri)
        alice_before = game_server._users.get_by_username("Alice").rating
        bob_before = game_server._users.get_by_username("Bob").rating

        await white.close()
        await black.receive_until("player_disconnected")

        over = await _await_grace_expiry(clock, grace_ms, black)
        assert over["payload"]["winner"] == "b"
        assert over["payload"]["reason"] == "disconnect"
        assert over["payload"]["rated"] is True

        # Reconnect must not revive the finished game.
        revived = NetworkClient(uri)
        await revived.connect()
        await revived.login("Alice", "secret1")
        with pytest.raises(TimeoutError):
            await revived.receive_until("match_found", timeout=0.4)
        await revived.close()

        alice_after = game_server._users.get_by_username("Alice").rating
        bob_after = game_server._users.get_by_username("Bob").rating
        assert alice_after < alice_before
        assert bob_after > bob_before

        # Advance again — rating must not change a second time.
        clock.advance(grace_ms + 1)
        await asyncio.sleep(0.1)
        assert game_server._users.get_by_username("Alice").rating == alice_after
        assert game_server._users.get_by_username("Bob").rating == bob_after

        await black.close()
        assert game_server.registry.get(game_id) is not None
    finally:
        await _stop(game_server, server, database)


@pytest.mark.asyncio
async def test_duplicate_live_connection_does_not_duplicate_seat():
    game_server, server, port, database = await _start()
    uri = f"ws://127.0.0.1:{port}"
    try:
        white, black, game_id = await _match_two_players(uri)
        alice_id = game_server._users.get_by_username("Alice").id

        twin = NetworkClient(uri)
        await twin.connect()
        auth = await twin.login("Alice", "secret1")
        assert auth["type"] == "auth_ok"
        # Still live on the first connection — must not steal / duplicate the seat.
        with pytest.raises(TimeoutError):
            await twin.receive_until("match_found", timeout=0.4)

        match = game_server.registry.get(game_id)
        whites = [
            s for s in match._players.values() if s.user_id == alice_id
        ]
        assert len(whites) == 1
        assert whites[0].disconnected is False

        await twin.close()
        await white.close()
        await black.close()
    finally:
        await _stop(game_server, server, database)


@pytest.mark.asyncio
async def test_spectator_disconnect_keeps_game_alive():
    game_server, server, port, database = await _start()
    uri = f"ws://127.0.0.1:{port}"
    try:
        white = NetworkClient(uri)
        black = NetworkClient(uri)
        spectator = NetworkClient(uri)
        await white.connect()
        await black.connect()
        await spectator.connect()
        await white.register("Alice", "secret1")
        await black.register("Bob", "secret1")
        await spectator.register("Carol", "secret1")

        room = await white.create_room()
        room_id = room["payload"]["room_id"]
        game_id = room["payload"]["game_id"]
        await black.join_room(room_id)
        await white.receive_until("room_update")
        await black.receive_until("state_snapshot")

        spec = await spectator.join_room(room_id)
        assert spec["payload"]["role"] == SessionRole.SPECTATOR
        await spectator.receive_until("state_snapshot")

        await spectator.close()
        await asyncio.sleep(0.05)

        match = game_server.registry.get(game_id)
        assert match.spectator_count() == 0
        assert match.player_count() == 2
        assert not match.engine.is_game_over()

        move = await white.send_move("WPe2e4")
        assert move["type"] == "move_accepted"

        await white.close()
        await black.close()
    finally:
        await _stop(game_server, server, database)


@pytest.mark.asyncio
async def test_no_ghost_queue_sessions_after_lobby_disconnect():
    game_server, server, port, database = await _start()
    uri = f"ws://127.0.0.1:{port}"
    try:
        client = NetworkClient(uri)
        await client.connect()
        await client.register("Alice", "secret1")
        await client.close()
        await asyncio.sleep(0.05)

        assert game_server.matchmaker.queue_size == 0
        assert len(game_server._sessions) == 0
        assert len(game_server._connections) == 0
    finally:
        await _stop(game_server, server, database)


@pytest.mark.asyncio
async def test_grace_timeout_resigns_once_legacy_wall_clock():
    """Regression with SystemClock + short grace (no FakeClock)."""
    game_server, server, port, database = await _start(grace_ms=100)
    uri = f"ws://127.0.0.1:{port}"
    try:
        white, black, _game_id = await _match_two_players(uri)
        await white.close()
        await black.receive_until("player_disconnected")

        over = await black.receive_until("game_over", timeout=2.0)
        assert over["payload"]["winner"] == "b"
        assert over["payload"]["reason"] == "disconnect"

        with pytest.raises(TimeoutError):
            await black.receive_until("game_over", timeout=0.3)

        await black.close()
    finally:
        await _stop(game_server, server, database)


@pytest.mark.asyncio
async def test_reconnect_before_grace_keeps_game_alive_legacy():
    game_server, server, port, database = await _start(grace_ms=500)
    uri = f"ws://127.0.0.1:{port}"
    try:
        white, black, game_id = await _match_two_players(uri)

        await white.close()
        notice = await black.receive_until("player_disconnected")
        assert notice["payload"]["color"] == "w"
        assert notice["payload"]["grace_period_ms"] == 500

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
