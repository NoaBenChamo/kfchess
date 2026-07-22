import asyncio

import pytest
from websockets.asyncio.server import serve

from client.network_client import NetworkClient
from server.dal.database import Database
from server.game_server import GameServer
from server.matchmaker import FakeClock, Matchmaker


async def _start(database=None, matchmaker=None, start_ticks=True):
    game_server = GameServer(database=database, matchmaker=matchmaker, tick_ms=20)
    if start_ticks:
        await game_server.start()
    server = await serve(game_server.handler, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    return game_server, server, port


async def _stop(game_server, server):
    server.close()
    await server.wait_closed()
    await game_server.stop()


@pytest.mark.asyncio
async def test_two_players_play_request_get_match_found():
    game_server, server, port = await _start()
    uri = f"ws://127.0.0.1:{port}"
    try:
        async with NetworkClient(uri) as a, NetworkClient(uri) as b:
            assert (await a.register("Alice", "secret1"))["type"] == "auth_ok"
            assert (await b.register("Bob", "secret1"))["type"] == "auth_ok"

            waiting = await a.play_request()
            assert waiting["type"] == "request_ok"
            assert waiting["payload"]["status"] == "waiting"

            matched_b = await b.play_request()
            assert matched_b["type"] == "match_found"
            assert matched_b["payload"]["color"] == "b"

            matched_a = await a.receive_until("match_found")
            assert matched_a["payload"]["color"] == "w"
            assert matched_a["payload"]["game_id"] == matched_b["payload"]["game_id"]

            snap_a = await a.receive_until("state_snapshot")
            snap_b = await b.receive_until("state_snapshot")
            assert snap_a["payload"]["pieces"] == snap_b["payload"]["pieces"]

            move = await a.send_move("WPe2e4")
            assert move["type"] == "move_accepted"
    finally:
        await _stop(game_server, server)


@pytest.mark.asyncio
async def test_play_request_outside_elo_range_does_not_match():
    game_server, server, port = await _start()
    uri = f"ws://127.0.0.1:{port}"
    try:
        async with NetworkClient(uri) as a, NetworkClient(uri) as b:
            await a.register("Alice", "secret1")
            await b.register("Bob", "secret1")
            # Force rating gap via repository.
            users = game_server._users
            bob = users.get_by_username("Bob")
            users.update_rating(bob.id, 1500)

            # Refresh session rating by logging in again is hard mid-connection;
            # bind_user already set 1200. Update session rating manually:
            for session in game_server._sessions.values():
                if session.username == "Bob":
                    session.rating = 1500

            wait_a = await a.play_request()
            wait_b = await b.play_request()
            assert wait_a["type"] == "request_ok"
            assert wait_b["type"] == "request_ok"
            assert game_server.matchmaker.queue_size == 2
    finally:
        await _stop(game_server, server)


@pytest.mark.asyncio
async def test_matchmaking_timeout_notifies_waiter():
    clock = FakeClock()
    matchmaker = Matchmaker(elo_range=100, timeout_ms=1000, clock=clock)
    database = Database(":memory:")
    database.connect()
    database.initialize_schema()
    game_server, server, port = await _start(
        database=database,
        matchmaker=matchmaker,
        start_ticks=False,
    )
    uri = f"ws://127.0.0.1:{port}"
    try:
        async with NetworkClient(uri) as client:
            await client.register("Alice", "secret1")
            waiting = await client.play_request()
            assert waiting["type"] == "request_ok"

            clock.advance(1000)
            await game_server._expire_matchmaking()

            timeout = await client.receive_until("matchmaking_timeout")
            assert timeout["type"] == "matchmaking_timeout"
            assert game_server.matchmaker.queue_size == 0
    finally:
        await _stop(game_server, server)
        database.close()


@pytest.mark.asyncio
async def test_cancel_matchmaking_removes_from_queue():
    game_server, server, port = await _start()
    uri = f"ws://127.0.0.1:{port}"
    try:
        async with NetworkClient(uri) as client:
            await client.register("Alice", "secret1")
            await client.play_request()
            assert game_server.matchmaker.queue_size == 1
            cancelled = await client.cancel_matchmaking()
            assert cancelled["payload"]["status"] == "cancelled"
            assert game_server.matchmaker.queue_size == 0
    finally:
        await _stop(game_server, server)
