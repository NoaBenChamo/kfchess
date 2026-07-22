"""Exit Game / return-to-lobby flow tests."""

import asyncio

import pytest
from websockets.asyncio.server import serve

from client.network_client import NetworkClient
from client.remote_ui import run_remote_ui
from server.dal.database import Database
from server.game_server import GameServer
from view.game_runner import GameRunner


async def _start():
    database = Database(":memory:")
    database.connect()
    database.initialize_schema()
    game_server = GameServer(database=database, tick_ms=20)
    await game_server.start()
    server = await serve(game_server.handler, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    return game_server, server, port, database


async def _stop(game_server, server, database):
    server.close()
    await server.wait_closed()
    await game_server.stop()
    database.close()


async def _match_two(uri):
    white = NetworkClient(uri)
    black = NetworkClient(uri)
    await white.connect()
    await black.connect()
    await white.register("Alice", "secret1")
    await black.register("Bob", "secret1")
    waiting = await white.play_request()
    assert waiting["type"] == "request_ok"
    matched_b = await black.play_request()
    assert matched_b["type"] == "match_found"
    await white.receive_until("match_found")
    await white.receive_until("state_snapshot")
    await black.receive_until("state_snapshot")
    return white, black, matched_b["payload"]["game_id"]


@pytest.mark.asyncio
async def test_player_leave_game_forfeits_and_updates_rating_once():
    game_server, server, port, database = await _start()
    uri = f"ws://127.0.0.1:{port}"
    try:
        white, black, game_id = await _match_two(uri)
        alice_before = game_server._users.get_by_username("Alice").rating
        bob_before = game_server._users.get_by_username("Bob").rating

        leave = await white.leave_game()
        # Broadcast order may deliver game_over before leave_ok to the leaver.
        if leave["type"] == "game_over":
            over_white = leave
            leave_ok = await white.receive_until("leave_ok", timeout=1.0)
            over = await black.receive_until("game_over", timeout=2.0)
            assert over_white["payload"]["winner"] == over["payload"]["winner"]
        else:
            leave_ok = leave
            over = await black.receive_until("game_over", timeout=2.0)

        assert leave_ok["type"] == "leave_ok"
        assert leave_ok["payload"].get("forfeit") is True
        assert over["payload"]["winner"] == "b"
        assert over["payload"]["reason"] == "disconnect"
        assert over["payload"]["rated"] is True

        alice_after = game_server._users.get_by_username("Alice").rating
        bob_after = game_server._users.get_by_username("Bob").rating
        assert alice_after < alice_before
        assert bob_after > bob_before

        # No second game_over / rating mutation.
        with pytest.raises(TimeoutError):
            await black.receive_until("game_over", timeout=0.3)
        assert game_server._users.get_by_username("Alice").rating == alice_after
        assert game_server._users.get_by_username("Bob").rating == bob_after

        match = game_server.registry.get(game_id)
        assert match.player_count() == 0

        await white.close()
        await black.close()
    finally:
        await _stop(game_server, server, database)


@pytest.mark.asyncio
async def test_spectator_leave_game_does_not_end_match():
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
        assert spec["payload"]["role"] == "spectator"
        await spectator.receive_until("state_snapshot")

        left = await spectator.leave_game()
        assert left["type"] == "leave_ok"
        assert left["payload"]["role"] == "spectator"

        match = game_server.registry.get(game_id)
        assert match.spectator_count() == 0
        assert match.player_count() == 2
        assert not match.engine.is_game_over()

        move = await white.send_move("WPe2e4")
        assert move["type"] == "move_accepted"

        await white.close()
        await black.close()
        await spectator.close()
    finally:
        await _stop(game_server, server, database)


@pytest.mark.asyncio
async def test_player_leave_clears_stale_room_membership_on_waiting_room():
    game_server, server, port, database = await _start()
    uri = f"ws://127.0.0.1:{port}"
    try:
        creator = NetworkClient(uri)
        await creator.connect()
        await creator.register("Alice", "secret1")
        room = await creator.create_room()
        room_id = room["payload"]["room_id"]
        game_id = room["payload"]["game_id"]

        left = await creator.leave_game()
        assert left["type"] == "leave_ok"
        assert game_server.rooms.get(room_id) is None
        assert game_server.registry.get(game_id) is None

        await creator.close()
    finally:
        await _stop(game_server, server, database)


def test_remote_ui_returns_to_startup_after_game_over(monkeypatch):
    """Application stays open: game over → StartupWindow again (not process exit)."""
    calls = {"startup": 0, "runner": 0}

    class _Result:
        def __init__(self):
            self.session = _FakeRemoteSession()

    class _FakeRemoteSession:
        connection_lost = False

        def stop(self):
            pass

    class _FakeRunner:
        def __init__(self, **kwargs):
            del kwargs
            self.return_to_lobby = True

        def run(self):
            calls["runner"] += 1

    def fake_startup(host, port):
        del host, port
        calls["startup"] += 1
        if calls["startup"] == 1:
            return _Result()
        return None  # user closes lobby on second visit

    monkeypatch.setattr("client.remote_ui.run_startup_window", fake_startup)
    monkeypatch.setattr("client.remote_ui.get_work_area", lambda: (1280, 900))
    monkeypatch.setattr(
        "client.remote_ui.create_ui",
        lambda w, h: type(
            "UI",
            (),
            {
                "renderer": object(),
                "board_mapper": object(),
                "layout": type("L", (), {"exit_button_rect": None})(),
            },
        )(),
    )
    monkeypatch.setattr("client.remote_ui.Controller", lambda *a, **k: object())
    monkeypatch.setattr("client.remote_ui.GameRunner", _FakeRunner)

    code = run_remote_ui("127.0.0.1", 8765)
    assert code == 2
    assert calls["startup"] == 2
    assert calls["runner"] == 1


def test_remote_ui_returns_to_startup_after_exit_game(monkeypatch):
    calls = {"startup": 0}

    class _Session:
        connection_lost = False
        leave_calls = 0

        def stop(self):
            pass

        def request_leave(self):
            self.leave_calls += 1

    class _Result:
        def __init__(self):
            self.session = _Session()

    class _FakeRunner:
        def __init__(self, **kwargs):
            self._session = kwargs["session"]
            self.return_to_lobby = False

        def run(self):
            self._session.request_leave()
            self.return_to_lobby = True

    def fake_startup(host, port):
        del host, port
        calls["startup"] += 1
        if calls["startup"] == 1:
            return _Result()
        return None

    monkeypatch.setattr("client.remote_ui.run_startup_window", fake_startup)
    monkeypatch.setattr("client.remote_ui.get_work_area", lambda: (1280, 900))
    monkeypatch.setattr(
        "client.remote_ui.create_ui",
        lambda w, h: type(
            "UI",
            (),
            {
                "renderer": object(),
                "board_mapper": object(),
                "layout": type("L", (), {"exit_button_rect": None})(),
            },
        )(),
    )
    monkeypatch.setattr("client.remote_ui.Controller", lambda *a, **k: object())
    monkeypatch.setattr("client.remote_ui.GameRunner", _FakeRunner)

    assert run_remote_ui("127.0.0.1", 9) == 2
    assert calls["startup"] == 2
