import asyncio

import pytest
from websockets.asyncio.server import serve

from client.network_client import NetworkClient
from engine.game_engine import GameEngine
from model.board import Board
from model.piece import Piece
from model.position import Position
from realtime.move import Move
from server.dal.database import Database
from server.dal.repositories import UserRepository
from server.game_registry import GameRegistry
from server.game_server import GameServer
from server.match import Match


async def _start(registry, database, tick_ms=20):
    game_server = GameServer(
        registry=registry,
        database=database,
        tick_ms=tick_ms,
    )
    await game_server.start()
    server = await serve(game_server.handler, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    return game_server, server, port


async def _stop(game_server, server, database):
    server.close()
    await server.wait_closed()
    await game_server.stop()
    database.close()


@pytest.mark.asyncio
async def test_rated_game_over_updates_db_and_notifies_clients():
    database = Database(":memory:")
    database.connect()
    database.initialize_schema()

    board = Board([
        [Piece("b", "K")],
        [Piece("w", "P")],
    ])
    engine = GameEngine(board)
    engine.start_game()

    registry = GameRegistry()
    match = Match("default", engine=engine)
    registry.register(match)

    game_server, server, port = await _start(registry, database)
    uri = f"ws://127.0.0.1:{port}"
    try:
        async with NetworkClient(uri) as white, NetworkClient(uri) as black:
            auth_w = await white.register("Alice", "secret1")
            auth_b = await black.register("Bob", "secret1")
            assert auth_w["type"] == "auth_ok"
            assert auth_b["type"] == "auth_ok"

            identity_w = await white.identify("Alice")
            assert identity_w["type"] == "identity_assigned"
            await white.receive_until("state_snapshot")

            identity_b = await black.identify("Bob")
            assert identity_b["type"] == "identity_assigned"
            await black.receive_until("state_snapshot")

            assert match.db_game_id is not None
            assert match.rated is True

            pawn = match.engine.get_board().get(Position(1, 0))
            now = match.engine._arbiter.get_time()
            async with match.lock:
                match.engine._arbiter.add_move(
                    Move(
                        pawn,
                        Position(1, 0),
                        Position(0, 0),
                        start_time=now,
                        duration=40,
                    )
                )

            over_w = await white.receive_until("game_over", timeout=3.0)
            over_b = await black.receive_until("game_over", timeout=3.0)

            assert over_w["payload"]["rated"] is True
            assert over_w["payload"]["winner"] == "w"
            assert over_w["payload"]["ratings"]["w"]["rating_after"] > 1200
            assert over_w["payload"]["ratings"]["b"]["rating_after"] < 1200
            assert over_b["payload"]["game_id"] == match.db_game_id

        users = UserRepository(database)
        assert users.get_by_username("Alice").rating > 1200
        assert users.get_by_username("Bob").rating < 1200
    finally:
        await _stop(game_server, server, database)
