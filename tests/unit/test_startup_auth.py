"""Tests for StartupWindow authentication / registration flow."""

import asyncio
import threading
from contextlib import contextmanager

from websockets.asyncio.server import serve

from client.remote_session import MODE_CREATE_ROOM, RemoteSession
from client.startup_window import (
    PHASE_AUTH,
    PHASE_LOBBY,
    StartupWindow,
)
from server.auth_service import AuthError
from server.dal.database import Database
from server.game_server import GameServer
from shared.protocol import INVALID_CREDENTIALS, USERNAME_TAKEN


class _LiveServer:
    """WebSocket GameServer on a background thread (own event loop)."""

    def __init__(self):
        self.host = "127.0.0.1"
        self.port = None
        self.game_server = None
        self._database = None
        self._ready = threading.Event()
        self._stop = threading.Event()
        self._error = None
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self._thread.start()
        if not self._ready.wait(timeout=10):
            raise RuntimeError(f"server failed to start: {self._error}")
        if self._error is not None:
            raise RuntimeError(self._error)

    def stop(self):
        self._stop.set()
        self._thread.join(timeout=10)

    def _run(self):
        try:
            asyncio.run(self._async_main())
        except Exception as exc:  # pragma: no cover - startup failure path
            self._error = str(exc)
            self._ready.set()

    async def _async_main(self):
        database = Database(":memory:")
        database.connect()
        database.initialize_schema()
        self._database = database
        game_server = GameServer(database=database, tick_ms=20)
        self.game_server = game_server
        await game_server.start()
        server = await serve(game_server.handler, self.host, 0)
        self.port = server.sockets[0].getsockname()[1]
        self._ready.set()
        try:
            while not self._stop.is_set():
                await asyncio.sleep(0.05)
        finally:
            server.close()
            await server.wait_closed()
            await game_server.stop()
            database.close()


@contextmanager
def live_server():
    srv = _LiveServer()
    srv.start()
    try:
        yield srv
    finally:
        srv.stop()


def _window(host, port, username="Alice", password="secret1"):
    window = StartupWindow(host, port)
    window._username = username
    window._password = password
    return window


def test_register_through_startup_auth_reaches_lobby_and_uses_login_after():
    with live_server() as srv:
        window = _window(srv.host, srv.port)
        window._go_lobby("register")
        assert window._phase == "authing"
        assert window._pending_auth_mode == "register"

        window._tick_auth()

        assert window._phase == PHASE_LOBBY
        assert window._error == ""
        # Critical: subsequent play sessions must login, not re-register.
        assert window._auth_mode == "login"

        user = srv.game_server._users.get_by_username("Alice")
        assert user is not None
        assert user.rating == 1200


def test_register_duplicate_username_stays_on_auth_with_error():
    with live_server() as srv:
        first = _window(srv.host, srv.port)
        first._go_lobby("register")
        first._tick_auth()
        assert first._phase == PHASE_LOBBY

        second = _window(srv.host, srv.port, username="Alice", password="other1")
        second._go_lobby("register")
        second._tick_auth()

        assert second._phase == PHASE_AUTH
        assert USERNAME_TAKEN in second._error


def test_register_rejects_empty_username_without_network():
    window = _window("127.0.0.1", 1, username="  ", password="secret1")
    window._go_lobby("register")
    assert window._phase == PHASE_AUTH
    assert "Username is required" in window._error


def test_register_rejects_empty_password_without_network():
    window = _window("127.0.0.1", 1, username="Alice", password="")
    window._go_lobby("register")
    assert window._phase == PHASE_AUTH
    assert "Password is required" in window._error


def test_register_short_password_shows_server_error():
    with live_server() as srv:
        window = _window(srv.host, srv.port, password="ab")
        window._go_lobby("register")
        window._tick_auth()

        assert window._phase == PHASE_AUTH
        assert INVALID_CREDENTIALS in window._error or "password" in window._error.lower()


def test_register_connection_failure_shows_error():
    # No server listening on this port.
    window = _window("127.0.0.1", 1)
    window._go_lobby("register")
    window._tick_auth()

    assert window._phase == PHASE_AUTH
    assert "CONNECTION_ERROR" in window._error


def test_register_database_failure_shows_error():
    with live_server() as srv:
        def _boom(username, password):
            raise AuthError("DATABASE_ERROR", "database unavailable")

        srv.game_server._auth.register = _boom

        window = _window(srv.host, srv.port)
        window._go_lobby("register")
        window._tick_auth()

        assert window._phase == PHASE_AUTH
        assert "DATABASE_ERROR" in window._error
        assert "database unavailable" in window._error


def test_after_register_play_session_uses_login_not_register():
    """Regression: re-register on Matchmaking/Create Room caused USERNAME_TAKEN."""
    import time

    with live_server() as srv:
        window = _window(srv.host, srv.port)
        window._go_lobby("register")
        window._tick_auth()
        assert window._auth_mode == "login"

        session = RemoteSession(
            f"ws://{srv.host}:{srv.port}",
            username=window._username,
            password=window._password,
            auth_mode=window._auth_mode,
            play_mode=MODE_CREATE_ROOM,
        )
        # Private room with one seat never becomes "ready"; wait for room_update.
        session.start_async()
        try:
            deadline = time.monotonic() + 10.0
            while time.monotonic() < deadline:
                session.pump(0)
                if session._startup_error is not None:
                    break
                if session.state.room_id is not None:
                    break
                time.sleep(0.02)

            assert session._startup_error is None, session._startup_error
            assert session.state.username == "Alice"
            assert session.state.room_id is not None
        finally:
            session.stop()
