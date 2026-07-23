"""Tests for StartupWindow authentication / registration flow."""

import time
from contextlib import contextmanager

from client.remote_session import MODE_CREATE_ROOM, RemoteSession
from client.startup_window import (
    PHASE_AUTH,
    PHASE_LOBBY,
    StartupWindow,
)
from server.auth_service import AuthError
from shared.protocol import INVALID_CREDENTIALS, USERNAME_TAKEN
from tests.e2e.harness import live_server


@contextmanager
def _live_server():
    with live_server() as srv:
        yield srv


def _window(host, port, username="Alice", password="secret1"):
    window = StartupWindow(host, port)
    window._username = username
    window._password = password
    return window


def test_register_through_startup_auth_reaches_lobby_and_uses_login_after():
    with _live_server() as srv:
        window = _window(srv.host, srv.port)
        window.handle_register()
        assert window.phase == "authing"
        assert window._pending_auth_mode == "register"

        window.tick()

        assert window.phase == PHASE_LOBBY
        assert window.error == ""
        # Critical: subsequent play sessions must login, not re-register.
        assert window._auth_mode == "login"

        user = srv.game_server._users.get_by_username("Alice")
        assert user is not None
        assert user.rating == 1200


def test_register_duplicate_username_stays_on_auth_with_error():
    with _live_server() as srv:
        first = _window(srv.host, srv.port)
        first.handle_register()
        first.tick()
        assert first.phase == PHASE_LOBBY

        second = _window(srv.host, srv.port, username="Alice", password="other1")
        second.handle_register()
        second.tick()

        assert second.phase == PHASE_AUTH
        assert USERNAME_TAKEN in second.error


def test_register_rejects_empty_username_without_network():
    window = _window("127.0.0.1", 1, username="  ", password="secret1")
    window.handle_register()
    assert window.phase == PHASE_AUTH
    assert "Username is required" in window.error


def test_register_rejects_empty_password_without_network():
    window = _window("127.0.0.1", 1, username="Alice", password="")
    window.handle_register()
    assert window.phase == PHASE_AUTH
    assert "Password is required" in window.error


def test_register_short_password_shows_server_error():
    with _live_server() as srv:
        window = _window(srv.host, srv.port, password="ab")
        window.handle_register()
        window.tick()

        assert window.phase == PHASE_AUTH
        assert INVALID_CREDENTIALS in window.error or "password" in window.error.lower()


def test_register_connection_failure_shows_error():
    # No server listening on this port.
    window = _window("127.0.0.1", 1)
    window.handle_register()
    window.tick()

    assert window.phase == PHASE_AUTH
    assert "CONNECTION_ERROR" in window.error


def test_register_database_failure_shows_error():
    with _live_server() as srv:
        def _boom(username, password):
            raise AuthError("DATABASE_ERROR", "database unavailable")

        srv.game_server._auth.register = _boom

        window = _window(srv.host, srv.port)
        window.handle_register()
        window.tick()

        assert window.phase == PHASE_AUTH
        assert "DATABASE_ERROR" in window.error
        assert "database unavailable" in window.error


def test_after_register_play_session_uses_login_not_register():
    """Regression: re-register on Matchmaking/Create Room caused USERNAME_TAKEN."""
    with _live_server() as srv:
        window = _window(srv.host, srv.port)
        window.handle_register()
        window.tick()
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


def test_login_via_handle_click_on_login_button():
    with _live_server() as srv:
        prep = _window(srv.host, srv.port)
        prep.handle_register()
        prep.tick()

        window = _window(srv.host, srv.port)
        window.handle_click(200, 270)  # Login button
        assert window.phase == "authing"
        window.tick()
        assert window.phase == PHASE_LOBBY
