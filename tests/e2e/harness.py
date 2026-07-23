"""Shared helpers for E2E tests: in-memory DB, FakeClock, live WebSocket server."""

import asyncio
import threading
import time
from contextlib import asynccontextmanager, contextmanager

from websockets.asyncio.server import serve

from client.network_client import NetworkClient
from client.startup_window import (
    PHASE_AUTH,
    PHASE_LOBBY,
    StartupWindow,
)
from server.clock import FakeClock
from server.config import MATCHMAKING_TIMEOUT_MS
from server.dal.database import Database
from server.game_server import GameServer
from server.matchmaker import Matchmaker


async def start_game_server(
    *,
    database=None,
    matchmaker=None,
    clock=None,
    tick_ms=20,
    disconnect_grace_ms=60_000,
    start_ticks=True,
    registry=None,
):
    """Spin up GameServer + ephemeral WebSocket listener. Returns (gs, server, port, db)."""
    owns_db = database is None
    if database is None:
        database = Database(":memory:")
        database.connect()
        database.initialize_schema()

    if matchmaker is None and clock is not None:
        matchmaker = Matchmaker(
            elo_range=100,
            timeout_ms=MATCHMAKING_TIMEOUT_MS,
            clock=clock,
        )

    kwargs = {
        "database": database,
        "tick_ms": tick_ms,
        "disconnect_grace_ms": disconnect_grace_ms,
    }
    if clock is not None:
        kwargs["clock"] = clock
    if matchmaker is not None:
        kwargs["matchmaker"] = matchmaker
    if registry is not None:
        kwargs["registry"] = registry

    game_server = GameServer(**kwargs)
    if start_ticks:
        await game_server.start()
    server = await serve(game_server.handler, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    return game_server, server, port, database, owns_db


async def stop_game_server(game_server, server, database, owns_db):
    server.close()
    await server.wait_closed()
    await game_server.stop()
    if owns_db:
        database.close()


@asynccontextmanager
async def e2e_server(**kwargs):
    game_server, server, port, database, owns_db = await start_game_server(**kwargs)
    try:
        yield game_server, f"ws://127.0.0.1:{port}", port, database
    finally:
        await stop_game_server(game_server, server, database, owns_db)


class LiveServer:
    """Background-thread GameServer for sync StartupWindow tests."""

    def __init__(self, clock=None, matchmaker=None):
        self.host = "127.0.0.1"
        self.port = None
        self.game_server = None
        self.clock = clock
        self._matchmaker = matchmaker
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
        except Exception as exc:  # pragma: no cover
            self._error = str(exc)
            self._ready.set()

    async def _async_main(self):
        database = Database(":memory:")
        database.connect()
        database.initialize_schema()
        kwargs = {"database": database, "tick_ms": 20}
        if self.clock is not None:
            kwargs["clock"] = self.clock
        if self._matchmaker is not None:
            kwargs["matchmaker"] = self._matchmaker
        elif self.clock is not None:
            kwargs["matchmaker"] = Matchmaker(
                elo_range=100,
                timeout_ms=MATCHMAKING_TIMEOUT_MS,
                clock=self.clock,
            )
        game_server = GameServer(**kwargs)
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
def live_server(**kwargs):
    srv = LiveServer(**kwargs)
    srv.start()
    try:
        yield srv
    finally:
        srv.stop()


def make_startup_window(host, port, username="", password=""):
    window = StartupWindow(host, port)
    window._username = username
    window._password = password
    return window


def type_text(window, text):
    for ch in text:
        window.handle_key(ord(ch))


def auth_via_handlers(window, mode="register"):
    """Drive register/login through the public handle_* API and tick auth."""
    if mode == "register":
        window.handle_register()
    else:
        window.handle_login()
    assert window.phase == "authing"
    window.tick()
    return window


async def register_pair(uri, name_a="Alice", name_b="Bob", password="secret1"):
    a = NetworkClient(uri)
    b = NetworkClient(uri)
    await a.connect()
    await b.connect()
    assert (await a.register(name_a, password))["type"] == "auth_ok"
    assert (await b.register(name_b, password))["type"] == "auth_ok"
    return a, b


async def matchmake_pair(uri, name_a="Alice", name_b="Bob", password="secret1"):
    a, b = await register_pair(uri, name_a, name_b, password)
    waiting = await a.play_request()
    assert waiting["type"] == "request_ok"
    matched_b = await b.play_request()
    assert matched_b["type"] == "match_found"
    matched_a = await a.receive_until("match_found")
    snap_a = await a.receive_until("state_snapshot")
    snap_b = await b.receive_until("state_snapshot")
    return a, b, matched_a, matched_b, snap_a, snap_b


async def wait_for_move_in_history(
    client,
    *,
    color="w",
    move_type=None,
    timeout=3.0,
    initial_payload=None,
):
    """Poll snapshots until a move appears in white/black history."""
    key = "white_moves" if color == "w" else "black_moves"

    def _match(payload):
        moves = payload.get(key) or []
        if not moves:
            return False
        return move_type is None or moves[-1].get("move_type") == move_type

    if initial_payload is not None and _match(initial_payload):
        return {"type": "state_snapshot", "payload": initial_payload}

    deadline = asyncio.get_running_loop().time() + timeout
    while asyncio.get_running_loop().time() < deadline:
        remaining = deadline - asyncio.get_running_loop().time()
        try:
            msg = await asyncio.wait_for(
                client.receive_message(), timeout=min(0.5, remaining)
            )
        except TimeoutError:
            continue
        if msg["type"] != "state_snapshot":
            continue
        if _match(msg["payload"]):
            return msg
    raise TimeoutError(f"timed out waiting for {color} move history ({move_type})")


async def wait_for_piece(
    client,
    *,
    row,
    col,
    color="w",
    piece_type=None,
    idle_states=("idle", "short_rest", "long_rest"),
    timeout=3.0,
    initial_payload=None,
):
    """Poll until a stationary piece is at (row, col)."""

    def _found(payload):
        for piece in payload.get("pieces") or []:
            if piece["row"] != row or piece["col"] != col:
                continue
            if piece["color"].lower() != color.lower():
                continue
            if piece_type is not None and piece["piece_type"] != piece_type:
                continue
            if piece.get("state") in idle_states:
                return True
        return False

    if initial_payload is not None and _found(initial_payload):
        return {"type": "state_snapshot", "payload": initial_payload}

    deadline = asyncio.get_running_loop().time() + timeout
    while asyncio.get_running_loop().time() < deadline:
        remaining = deadline - asyncio.get_running_loop().time()
        try:
            msg = await asyncio.wait_for(
                client.receive_message(), timeout=min(0.5, remaining)
            )
        except TimeoutError:
            continue
        if msg["type"] != "state_snapshot":
            continue
        if _found(msg["payload"]):
            return msg
    raise TimeoutError(f"timed out waiting for piece at ({row},{col})")

def pump_until(session, predicate, timeout=10.0, interval=0.02):
    """Pump a RemoteSession until predicate(session) or timeout."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        session.pump(0)
        if predicate(session):
            return True
        time.sleep(interval)
    session.pump(0)
    return predicate(session)


# Re-exports used by tests
__all__ = [
    "FakeClock",
    "MATCHMAKING_TIMEOUT_MS",
    "PHASE_AUTH",
    "PHASE_LOBBY",
    "auth_via_handlers",
    "e2e_server",
    "live_server",
    "make_startup_window",
    "matchmake_pair",
    "pump_until",
    "register_pair",
    "type_text",
    "wait_for_move_in_history",
    "wait_for_piece",
]
