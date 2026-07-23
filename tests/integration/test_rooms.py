import asyncio

import pytest
from websockets.asyncio.server import serve

from client.network_client import NetworkClient
from server.dal.database import Database
from server.game_server import GameServer
from server.session_role_enum import SessionRole
from shared.protocol import ROOM_NOT_FOUND, SPECTATOR_READ_ONLY


async def _start():
    database = Database(":memory:")
    database.connect()
    database.initialize_schema()
    game_server = GameServer(database=database, tick_ms=20)
    await game_server.start()
    server = await serve(game_server.handler, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    return game_server, server, port


async def _stop(game_server, server):
    server.close()
    await server.wait_closed()
    await game_server.stop()


@pytest.mark.asyncio
async def test_create_room_unique_and_creator_is_white():
    game_server, server, port = await _start()
    uri = f"ws://127.0.0.1:{port}"
    try:
        async with NetworkClient(uri) as client:
            assert (await client.register("Alice", "secret1"))["type"] == "auth_ok"
            room = await client.create_room()
            assert room["type"] == "room_update"
            assert room["payload"]["role"] == SessionRole.PLAYER
            assert room["payload"]["color"] == "w"
            assert room["payload"]["room_id"]
            assert room["payload"]["players"]["w"]["username"] == "Alice"

            identity = await client.receive_until("identity_assigned")
            assert identity["payload"]["color"] == "w"
            await client.receive_until("match_found")
            await client.receive_until("state_snapshot")
    finally:
        await _stop(game_server, server)


@pytest.mark.asyncio
async def test_second_joiner_is_black_third_is_spectator_readonly():
    game_server, server, port = await _start()
    uri = f"ws://127.0.0.1:{port}"
    try:
        async with (
            NetworkClient(uri) as white,
            NetworkClient(uri) as black,
            NetworkClient(uri) as spectator,
        ):
            await white.register("Alice", "secret1")
            await black.register("Bob", "secret1")
            await spectator.register("Carol", "secret1")

            created = await white.create_room()
            room_id = created["payload"]["room_id"]
            await white.receive_until("identity_assigned")
            await white.receive_until("match_found")
            await white.receive_until("state_snapshot")

            joined_black = await black.join_room(room_id)
            assert joined_black["payload"]["role"] == SessionRole.PLAYER
            assert joined_black["payload"]["color"] == "b"
            await black.receive_until("identity_assigned")
            await black.receive_until("match_found")
            snap_black = await black.receive_until("state_snapshot")

            # Creator sees room_update when black joins.
            update = await white.receive_until("room_update")
            assert update["payload"]["players"]["b"]["username"] == "Bob"

            joined_spec = await spectator.join_room(room_id)
            assert joined_spec["payload"]["role"] == SessionRole.SPECTATOR
            assert "color" not in joined_spec["payload"]
            snap_spec = await spectator.receive_until("state_snapshot")
            assert snap_spec["payload"]["pieces"] == snap_black["payload"]["pieces"]

            denied = await spectator.send_move("WPe2e4")
            assert denied["type"] == "error"
            assert denied["payload"]["code"] == SPECTATOR_READ_ONLY

            move = await white.send_move("WPe2e4")
            assert move["type"] == "move_accepted"

            # Spectator receives the broadcast snapshot for the same move.
            broadcast = await spectator.receive_until("state_snapshot")
            assert broadcast["payload"]["sequence"] >= snap_spec["payload"]["sequence"]
            assert broadcast["payload"]["pieces"] != snap_spec["payload"]["pieces"]
    finally:
        await _stop(game_server, server)


@pytest.mark.asyncio
async def test_join_unknown_room_returns_not_found():
    game_server, server, port = await _start()
    uri = f"ws://127.0.0.1:{port}"
    try:
        async with NetworkClient(uri) as client:
            await client.register("Alice", "secret1")
            response = await client.join_room("ZZZZZZ")
            assert response["type"] == "error"
            assert response["payload"]["code"] == ROOM_NOT_FOUND
    finally:
        await _stop(game_server, server)


@pytest.mark.asyncio
async def test_broadcast_stays_inside_room():
    game_server, server, port = await _start()
    uri = f"ws://127.0.0.1:{port}"
    try:
        async with (
            NetworkClient(uri) as a,
            NetworkClient(uri) as b,
            NetworkClient(uri) as outsider,
        ):
            await a.register("Alice", "secret1")
            await b.register("Bob", "secret1")
            await outsider.register("Dan", "secret1")

            room_a = await a.create_room()
            await a.receive_until("identity_assigned")
            await a.receive_until("match_found")
            await a.receive_until("state_snapshot")

            room_b = await outsider.create_room()
            await outsider.receive_until("identity_assigned")
            await outsider.receive_until("match_found")
            await outsider.receive_until("state_snapshot")
            assert room_a["payload"]["room_id"] != room_b["payload"]["room_id"]

            await b.join_room(room_a["payload"]["room_id"])
            await b.receive_until("identity_assigned")
            await b.receive_until("match_found")
            await b.receive_until("state_snapshot")

            move = await a.send_move("WPe2e4")
            assert move["type"] == "move_accepted"
            snap_b = await b.receive_until("state_snapshot")
            assert snap_b["type"] == "state_snapshot"

            # Outsider in another room should not see A's move within a short window.
            with pytest.raises(TimeoutError):
                await outsider.receive_until("state_snapshot", timeout=0.3)
    finally:
        await _stop(game_server, server)
