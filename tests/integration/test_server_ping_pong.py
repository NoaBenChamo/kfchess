import asyncio

import pytest
from websockets.asyncio.client import connect
from websockets.asyncio.server import serve

from client.network_client import NetworkClient
from server.game_server import GameServer
from shared.protocol import (
    NOT_AUTHENTICATED,
    NOT_YOUR_PIECE,
    SERVER_FULL,
    USERNAME_TAKEN,
    decode_message,
    encode_message,
)
from shared.squares import square_to_position


async def _start_server(start_ticks=False, tick_ms=20):
    game_server = GameServer(tick_ms=tick_ms)
    if start_ticks:
        await game_server.start()
    server = await serve(game_server.handler, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    return game_server, server, port


async def _stop_server(game_server, server):
    server.close()
    await server.wait_closed()
    await game_server.stop()


async def _identify_as(client, username):
    response = await client.identify(username)
    assert response["type"] == "identity_assigned"
    # Drain the initial state_snapshot that follows identity_assigned.
    await client.receive_until("state_snapshot")
    return response


@pytest.mark.asyncio
async def test_ping_pong_roundtrip():
    game_server, server, port = await _start_server()
    try:
        async with NetworkClient(f"ws://127.0.0.1:{port}") as client:
            response = await client.ping()
        assert response["type"] == "pong"
        assert response["payload"] == {}
        await asyncio.sleep(0.05)
        assert game_server.connection_count == 0
    finally:
        await _stop_server(game_server, server)


@pytest.mark.asyncio
async def test_invalid_json_returns_error_without_killing_server():
    game_server, server, port = await _start_server()
    try:
        async with connect(f"ws://127.0.0.1:{port}") as websocket:
            await websocket.send("{not-json")
            error = decode_message(await websocket.recv())
            assert error["type"] == "error"
            assert error["payload"]["code"] == "INVALID_MESSAGE"

            await websocket.send(encode_message("ping"))
            pong = decode_message(await websocket.recv())
            assert pong["type"] == "pong"
    finally:
        await _stop_server(game_server, server)


@pytest.mark.asyncio
async def test_client_disconnect_keeps_server_alive():
    game_server, server, port = await _start_server()
    try:
        async with NetworkClient(f"ws://127.0.0.1:{port}") as client:
            await client.ping()
            assert game_server.connection_count == 1

        await asyncio.sleep(0.05)
        assert game_server.connection_count == 0

        async with NetworkClient(f"ws://127.0.0.1:{port}") as client:
            response = await client.ping()
            assert response["type"] == "pong"
    finally:
        await _stop_server(game_server, server)


@pytest.mark.asyncio
async def test_valid_move_returns_move_accepted():
    game_server, server, port = await _start_server()
    try:
        async with NetworkClient(f"ws://127.0.0.1:{port}") as client:
            await _identify_as(client, "Alice")
            response = await client.send_move("WPe2e4")

        assert response["type"] == "move_accepted"
        assert response["payload"]["command"] == "WPe2e4"
        assert "snapshot" in response["payload"]
        assert response["payload"]["snapshot"]["sequence"] == 1
        await asyncio.sleep(0.05)
        assert game_server.connection_count == 0
    finally:
        await _stop_server(game_server, server)


@pytest.mark.asyncio
async def test_invalid_move_command_returns_error():
    game_server, server, port = await _start_server()
    try:
        async with NetworkClient(f"ws://127.0.0.1:{port}") as client:
            await _identify_as(client, "Alice")
            response = await client.send_move("NOPE")

        assert response["type"] == "error"
        assert response["payload"]["code"] == "invalid_move_command"
    finally:
        await _stop_server(game_server, server)


@pytest.mark.asyncio
async def test_illegal_engine_move_returns_error():
    game_server, server, port = await _start_server()
    try:
        async with NetworkClient(f"ws://127.0.0.1:{port}") as client:
            await _identify_as(client, "Alice")
            response = await client.send_move("WPe2e5")

        assert response["type"] == "error"
        assert response["payload"]["code"] == "INVALID_MOVE"
    finally:
        await _stop_server(game_server, server)


@pytest.mark.asyncio
async def test_ping_still_works_after_move_handling():
    game_server, server, port = await _start_server()
    try:
        async with NetworkClient(f"ws://127.0.0.1:{port}") as client:
            await _identify_as(client, "Alice")
            move_response = await client.send_move("WPe2e4")
            pong = await client.ping()

        assert move_response["type"] == "move_accepted"
        assert pong["type"] == "pong"
    finally:
        await _stop_server(game_server, server)


@pytest.mark.asyncio
async def test_server_tick_broadcasts_until_motion_settles():
    game_server, server, port = await _start_server(start_ticks=True, tick_ms=20)
    try:
        async with NetworkClient(f"ws://127.0.0.1:{port}") as client:
            await _identify_as(client, "Alice")
            accepted = await client.send_move("WPe2e4")
            assert accepted["type"] == "move_accepted"

            saw_snapshot = False
            deadline = asyncio.get_running_loop().time() + 1.5
            while asyncio.get_running_loop().time() < deadline:
                try:
                    message = await asyncio.wait_for(
                        client.receive_message(),
                        timeout=0.3,
                    )
                except asyncio.TimeoutError:
                    break
                if message["type"] == "state_snapshot":
                    saw_snapshot = True

            assert saw_snapshot is True

        match = game_server.registry.get("default")
        piece = match.engine.get_board().get(square_to_position("e4"))
        assert piece is not None
        assert piece.type == "P"
    finally:
        await _stop_server(game_server, server)


@pytest.mark.asyncio
async def test_two_clients_receive_same_snapshot_sequence():
    game_server, server, port = await _start_server()
    uri = f"ws://127.0.0.1:{port}"
    try:
        async with NetworkClient(uri) as client_a, NetworkClient(uri) as client_b:
            identity_a = await _identify_as(client_a, "Alice")
            identity_b = await _identify_as(client_b, "Bob")
            assert identity_a["payload"]["color"] == "w"
            assert identity_b["payload"]["color"] == "b"

            accepted = await client_a.send_move("WPe2e4")
            assert accepted["type"] == "move_accepted"
            sequence = accepted["payload"]["snapshot"]["sequence"]

            snap_a = await client_a.receive_until("state_snapshot")
            snap_b = await client_b.receive_until("state_snapshot")

            assert snap_a["payload"]["sequence"] == sequence
            assert snap_b["payload"]["sequence"] == sequence
            assert snap_a["payload"]["pieces"] == snap_b["payload"]["pieces"]
            assert snap_a["payload"]["white_score"] == snap_b["payload"]["white_score"]
    finally:
        await _stop_server(game_server, server)


@pytest.mark.asyncio
async def test_first_identify_is_white_second_is_black():
    game_server, server, port = await _start_server()
    uri = f"ws://127.0.0.1:{port}"
    try:
        async with NetworkClient(uri) as client_a, NetworkClient(uri) as client_b:
            a = await client_a.identify("Alice")
            b = await client_b.identify("Bob")
            assert a["payload"]["color"] == "w"
            assert b["payload"]["color"] == "b"
    finally:
        await _stop_server(game_server, server)


@pytest.mark.asyncio
async def test_third_identify_returns_server_full():
    game_server, server, port = await _start_server()
    uri = f"ws://127.0.0.1:{port}"
    try:
        async with (
            NetworkClient(uri) as client_a,
            NetworkClient(uri) as client_b,
            NetworkClient(uri) as client_c,
        ):
            await _identify_as(client_a, "Alice")
            await _identify_as(client_b, "Bob")
            response = await client_c.identify("Carol")
            assert response["type"] == "error"
            assert response["payload"]["code"] == SERVER_FULL
    finally:
        await _stop_server(game_server, server)


@pytest.mark.asyncio
async def test_duplicate_username_returns_username_taken():
    game_server, server, port = await _start_server()
    uri = f"ws://127.0.0.1:{port}"
    try:
        async with NetworkClient(uri) as client_a, NetworkClient(uri) as client_b:
            await _identify_as(client_a, "Alice")
            response = await client_b.identify("alice")
            assert response["type"] == "error"
            assert response["payload"]["code"] == USERNAME_TAKEN
    finally:
        await _stop_server(game_server, server)


@pytest.mark.asyncio
async def test_move_before_identify_returns_not_authenticated():
    game_server, server, port = await _start_server()
    try:
        async with NetworkClient(f"ws://127.0.0.1:{port}") as client:
            response = await client.send_move("WPe2e4")
        assert response["type"] == "error"
        assert response["payload"]["code"] == NOT_AUTHENTICATED
    finally:
        await _stop_server(game_server, server)


@pytest.mark.asyncio
async def test_white_cannot_move_black_piece():
    game_server, server, port = await _start_server()
    try:
        async with NetworkClient(f"ws://127.0.0.1:{port}") as client:
            await _identify_as(client, "Alice")
            response = await client.send_move("BPe7e5")
        assert response["type"] == "error"
        assert response["payload"]["code"] == NOT_YOUR_PIECE
    finally:
        await _stop_server(game_server, server)


@pytest.mark.asyncio
async def test_black_cannot_move_white_piece():
    game_server, server, port = await _start_server()
    uri = f"ws://127.0.0.1:{port}"
    try:
        async with NetworkClient(uri) as white, NetworkClient(uri) as black:
            await _identify_as(white, "Alice")
            await _identify_as(black, "Bob")
            response = await black.send_move("WPe2e4")
        assert response["type"] == "error"
        assert response["payload"]["code"] == NOT_YOUR_PIECE
    finally:
        await _stop_server(game_server, server)


@pytest.mark.asyncio
async def test_disconnect_frees_seat_for_next_player():
    game_server, server, port = await _start_server()
    uri = f"ws://127.0.0.1:{port}"
    try:
        async with NetworkClient(uri) as client_a:
            await _identify_as(client_a, "Alice")
            async with NetworkClient(uri) as client_b:
                await _identify_as(client_b, "Bob")

        await asyncio.sleep(0.05)
        match = game_server.registry.get("default")
        assert match.player_count() == 0

        async with NetworkClient(uri) as client_c:
            identity = await _identify_as(client_c, "Carol")
            assert identity["payload"]["color"] == "w"
    finally:
        await _stop_server(game_server, server)
